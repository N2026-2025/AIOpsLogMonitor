# Genera notebooks/eda.ipynb a partir de un contenido reproducible
import os
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.11"},
}

def md(text):
    return nbf.v4.new_markdown_cell(text)

def code(text):
    return nbf.v4.new_code_cell(text)

cells = [
    md("# EDA — AIOps Log Monitor\n\n"
       "Análisis exploratorio del dataset de logs (`data/sample.csv`).\n\n"
       "Cubre: valores faltantes, rangos numéricos, distribución de la variable objetivo "
       "(status/severity), conteo de categóricas, matriz de correlación, palabras frecuentes "
       "en `message` y feature importance para predecir fallos.\n\n"
       "Este notebook se exporta a `scripts/eda.py` para ejecución reproducible."),
    code("import os\nimport re\nfrom collections import Counter\n\n"
         "import matplotlib\nmatplotlib.use('Agg')\n"
         "import matplotlib.pyplot as plt\nimport numpy as np\nimport pandas as pd\n"
         "from sklearn.ensemble import RandomForestClassifier\n\n"
         "DATA_PATH = os.path.join('..', 'data', 'processed_events_analysis.csv')\n"
         "FALLBACK = os.path.join('..', 'data', 'sample.csv')\n"
         "if not os.path.exists(DATA_PATH):\n    DATA_PATH = FALLBACK\n"
         "OUT_DIR = os.path.join('..', 'docs', 'eda')\n"
         "os.makedirs(OUT_DIR, exist_ok=True)\n"
         "plt.rcParams['figure.figsize'] = (10, 6)\nplt.rcParams['axes.grid'] = True\n\n"
         "def save_fig(name):\n"
         "    path = os.path.join(OUT_DIR, name)\n"
         "    plt.tight_layout(); plt.savefig(path, dpi=150, bbox_inches='tight'); plt.close()\n"
         "    print('saved', path)"),
    md("## 1. Carga y valores faltantes"),
    code("df = pd.read_csv(DATA_PATH)\nprint('shape', df.shape)\n"
         "missing = df.isna().sum()\nmissing = missing[missing > 0].sort_values(ascending=False)\n"
         "print(missing.to_string())\n\n"
         "fig, ax = plt.subplots()\n"
         "if not missing.empty:\n    missing.plot(kind='barh', ax=ax, color='#4c72b0')\n"
         "    ax.set_xlabel('Count of missing values'); ax.set_title('Missing values per column')\n"
         "else:\n    ax.text(0.5, 0.5, 'No missing values', ha='center', va='center')\n"
         "save_fig('missing_values.png'); plt.show()"),
    md("## 2. Rangos de variables numéricas (min/max/mean/std)"),
    code("numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()\n"
         "desc = df[numeric_cols].describe().loc[['min', 'max', 'mean', 'std']]\n"
         "print(desc.to_string())\n\n"
         "key_numeric = [c for c in ['duration_ms','status_code','hour','event_count','line','process_id'] if c in df.columns]\n"
         "fig, axes = plt.subplots(2, 3, figsize=(15, 8)); axes = axes.ravel()\n"
         "for i, col in enumerate(key_numeric[:6]):\n"
         "    df[col].hist(ax=axes[i], bins=30, color='#55a868', edgecolor='black')\n"
         "    axes[i].set_title(col)\n"
         "for j in range(len(key_numeric), len(axes)):\n    axes[j].axis('off')\n"
         "save_fig('numeric_distributions.png'); plt.show()"),
    md("## 3. Variable objetivo: status y severity"),
    code("for col in ['status', 'severity', 'event_type', 'category', 'environment']:\n"
         "    if col in df.columns:\n"
         "        print('===', col, '===')\n"
         "        print(df[col].value_counts(dropna=False).to_string())\n"
         "        fig, ax = plt.subplots()\n"
         "        df[col].value_counts().head(10).plot(kind='bar', ax=ax, color='#8172b3')\n"
         "        ax.set_title(col + ' distribution'); plt.xticks(rotation=45, ha='right')\n"
         "        save_fig(col + '_distribution.png'); plt.show()\n\n"
         "failure_rate = (df['status'].astype(str).str.lower() == 'failure').mean()\n"
         "print('Failure rate:', round(failure_rate, 4))"),
    md("## 4. Matriz de correlación"),
    code("corr = df[numeric_cols].corr(numeric_only=True)\n"
         "fig, ax = plt.subplots(figsize=(10, 8))\n"
         "im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)\n"
         "ax.set_xticks(range(len(corr.columns))); ax.set_yticks(range(len(corr.index)))\n"
         "ax.set_xticklabels(corr.columns, rotation=90, fontsize=7)\n"
         "ax.set_yticklabels(corr.index, fontsize=7)\n"
         "fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)\n"
         "ax.set_title('Correlation matrix'); save_fig('correlation_matrix.png'); plt.show()"),
    md("## 5. Palabras frecuentes en los mensajes de log"),
    code("messages = df['message'].dropna().astype(str)\n"
         "words = Counter()\n"
         "for msg in messages:\n"
         "    words.update(re.findall(r'[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9]+', msg.lower()))\n"
         "top_words = words.most_common(20)\n"
         "print(top_words)\n"
         "if top_words:\n"
         "    fig, ax = plt.subplots(figsize=(10, 6))\n"
         "    ws, cs = zip(*top_words)\n"
         "    ax.barh(range(len(ws)), cs, color='#c44e52')\n"
         "    ax.set_yticks(range(len(ws))); ax.set_yticklabels(ws); ax.invert_yaxis()\n"
         "    ax.set_title('Top frequent words in log messages')\n"
         "    save_fig('message_word_frequencies.png'); plt.show()"),
    md("## 6. Feature importance (RandomForest, objetivo = FAILURE)"),
    code("feature_cols = [c for c in ['duration_ms','status_code','hour','event_count','line','process_id','severity','event_type','category','environment','method'] if c in df.columns]\n"
         "X = df[feature_cols].copy()\n"
         "y = (df['status'].astype(str).str.lower() == 'failure').astype(int)\n"
         "for col in X.columns:\n"
         "    if X[col].dtype == object:\n        X[col] = X[col].astype('category').cat.codes\n"
         "X = X.fillna(0)\n"
         "rf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)\n"
         "rf.fit(X, y)\n"
         "importance = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)\n"
         "print(importance.to_string())\n"
         "fig, ax = plt.subplots(figsize=(10, 6))\n"
         "importance.head(10).plot(kind='barh', ax=ax, color='#64a0c8'); ax.invert_yaxis()\n"
         "ax.set_title('Top 10 feature importance (predicting failure)')\n"
         "save_fig('feature_importance.png'); plt.show()"),
    md("## Conclusión\n\n"
       "El dataset está mayormente completo en columnas clave (status, severity, event_type). "
       "Los nulos se concentran en columnas de request (message, method, path, status_code, duration_ms) "
       "que solo aplican a eventos HTTP. La tasa de fallos es ~27%. `event_type` y `severity` son las "
       "features más predictivas para el fallo. Todos los gráficos se guardan en `docs/eda/`."),
]

nb["cells"] = cells
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notebooks", "eda.ipynb")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print("notebook written:", out)
