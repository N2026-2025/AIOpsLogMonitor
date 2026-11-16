from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

output_path = r"C:\Sentinel-Grid\Entrevista_AIOps_Log_Monitor.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=1.8*cm,
    leftMargin=1.8*cm,
    topMargin=1.8*cm,
    bottomMargin=1.8*cm
)

styles = getSampleStyleSheet()

title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#1a237e'), spaceAfter=10, alignment=TA_CENTER)
subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#546e7a'), alignment=TA_CENTER, spaceAfter=16)
h1_style = ParagraphStyle('CustomH1', parent=styles['Heading1'], fontSize=15, textColor=colors.HexColor('#1a237e'), spaceBefore=16, spaceAfter=7, leading=18)
h2_style = ParagraphStyle('CustomH2', parent=styles['Heading2'], fontSize=12.5, textColor=colors.HexColor('#283593'), spaceBefore=12, spaceAfter=5, leading=15)
body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=5)
bullet_style = ParagraphStyle('CustomBullet', parent=styles['Normal'], fontSize=10, leading=13.5, leftIndent=16, bulletIndent=6, spaceAfter=3)
quote_style = ParagraphStyle('CustomQuote', parent=styles['Normal'], fontSize=9.5, leading=13, leftIndent=18, rightIndent=18, textColor=colors.HexColor('#37474f'), backColor=colors.HexColor('#e8eaf6'), borderPadding=6, spaceAfter=7)

cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=TA_LEFT)
cell_header_style = ParagraphStyle('CellHeader', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=TA_LEFT, textColor=colors.white, fontName='Helvetica-Bold')

def cell(text, style=cell_style):
    return Paragraph(text, style)

def cell_header(text):
    return Paragraph(text, cell_header_style)

def add_paragraph(text, style=body_style):
    return Paragraph(text, style)

def add_bullet(text):
    return Paragraph(text, bullet_style, bulletText='\u2022')

story = []

# Portada
story.append(Spacer(1, 2.5*cm))
story.append(Paragraph("Guía de Entrevista Técnica y Laboral", title_style))
story.append(Paragraph("Proyecto: AIOps Log Monitor / Legacy-Bridge", subtitle_style))
story.append(Paragraph("Documento de preparación para entrevista", ParagraphStyle('x', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER, textColor=colors.HexColor('#455a64'))))
story.append(Paragraph("Noviembre 2026", ParagraphStyle('x', parent=styles['Normal'], fontSize=9.5, alignment=TA_CENTER, textColor=colors.HexColor('#78909c'))))
story.append(PageBreak())

# Índice
story.append(Paragraph("Índice", h1_style))
for item in [
    "1. Resumen ejecutivo del proyecto",
    "2. Por qué es un buen proyecto para la entrevista",
    "3. Preguntas técnicas usuales sobre este proyecto",
    "4. Preguntas que hacen los reclutadores (primera criba)",
    "5. Cómo presentarlo: marco de 4-5 minutos",
    "6. Consejos clave para la entrevista",
    "7. Plan de preparación recomendado",
]:
    story.append(Paragraph(item, body_style))
story.append(PageBreak())

# 1. Resumen ejecutivo
story.append(Paragraph("1. Resumen ejecutivo del proyecto", h1_style))
story.append(add_paragraph("El proyecto <b>AIOps Log Monitor / Legacy-Bridge</b> es un sistema que lee automáticamente los logs de programas antiguos (sistemas legacy), los analiza con inteligencia artificial explicable y avisa al equipo de soporte cuáles incidentes son críticos, para que no tengan que revisar miles de líneas a mano."))
story.append(Paragraph("El problema que resuelve", h2_style))
for b in [
    "Hasta el 70% del presupuesto IT de muchas empresas se gasta manteniendo sistemas antiguos.",
    "Esos sistemas generan miles de eventos por minuto en logs.",
    "Los equipos de soporte, QA y desarrollo pierden horas revisando logs manualmente para encontrar por qué cayó un servicio.",
    "Hay degradaciones silenciosas (picos de latencia) que disparan costos de servidores sin ser detectadas.",
]:
    story.append(add_bullet(b))
story.append(Paragraph("Cómo funciona (flujo simplificado)", h2_style))
story.append(add_paragraph("<font face='Courier'>Logs de sistemas antiguos → Limpieza y preparación → Base de datos → Modelo de ML (predice fallos) → Explicación con SHAP (por qué dice que es fallo) → API REST que el equipo de soporte consulta</font>"))
story.append(Paragraph("Las 5 capas del proyecto", h2_style))
layers = [
    [cell_header("Capa"), cell_header("Qué hace"), cell_header("Tecnología")],
    [cell("Ingesta"), cell("Limpia archivos CSV de logs y prepara los datos"), cell("Python")],
    [cell("Almacenamiento"), cell("Guarda los eventos organizados por entorno, instancia y servicio"), cell("PostgreSQL + SQLAlchemy")],
    [cell("Modelado ML"), cell("Predice si habrá un fallo y detecta anomalías"), cell("RandomForest + IsolationForest")],
    [cell("Explicabilidad"), cell("Explica por qué el modelo tomó esa decisión (no es caja negra)"), cell("SHAP")],
    [cell("API REST"), cell("Expone endpoints para consultar incidentes priorizados"), cell("FastAPI")],
]
table = Table(layers, colWidths=[2.8*cm, 8.2*cm, 5.2*cm], repeatRows=1)
table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(table)
story.append(PageBreak())

# 2. Por qué es un buen proyecto
story.append(Paragraph("2. Por qué es un buen proyecto para la entrevista", h1_style))
story.append(add_paragraph("Según lo que los reclutadores evalúan hoy (guías de 2025-2026), este proyecto tiene justo lo que piden:"))
recruiter_table = [
    [cell_header("Lo que buscan"), cell_header("Cómo lo cumple tu proyecto")],
    [cell("Problema real de negocio"), cell("Sistemas legacy cuestan hasta 70% del presupuesto IT; ahorra horas de revisión manual de logs")],
    [cell("Pensamiento de sistema completo"), cell("Ingesta → DB → ML → explicabilidad → API → CI/CD → deploy")],
    [cell("ML interpretable (no caja negra)"), cell("Usa SHAP para justificar cada predicción")],
    [cell("Conciencia de producción"), cell("Observabilidad (Prometheus + alertas), seguridad (gitleaks/semgrep/trivy), deploy en Render")],
    [cell("Trade-offs justificados"), cell("Documenta por qué RandomForest+IsolationForest y no autoencoders")],
]
table2 = Table(recruiter_table, colWidths=[5.5*cm, 10.7*cm], repeatRows=1)
table2.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(table2)
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("<b>La clave:</b> los reclutadores no buscan el modelo más avanzado, buscan que sepas <b>contar una historia de decisiones</b>: por qué elegiste cada cosa y qué rechazaste. Un proyecto end-to-end vale más que 20 notebooks de Kaggle.", quote_style))
story.append(PageBreak())

# 3. Preguntas técnicas
story.append(Paragraph("3. Preguntas técnicas usuales sobre este proyecto", h1_style))
story.append(add_paragraph("Estas son las que un entrevistador técnico te hará profundizando en tu proyecto (project deep-dive). Las agrupé por tema:"))

story.append(Paragraph("Sobre el modelo de ML", h2_style))
for q in [
    "¿Por qué RandomForest + IsolationForest y no otro modelo? (Esperan: interpretabilidad, features mixtas, buen baseline, bajo costo).",
    "¿Cómo detectas anomalías con IsolationForest exactamente? (Aísla puntos raros con menos cortes aleatorios).",
    "¿Cómo entrenaste el modelo? ¿Qué features usaste? (event_type, severity, status, duration_ms, status_code, hour).",
    "El README dice accuracy = 1.0. ¿No te preocupa el overfitting o el data leakage? <b>Prepárate esta, es la más probable.</b>",
    "¿Cómo manejarías un dataset desbalanceado (pocos fallos, muchos OK)?",
    "¿Qué métricas usaste además de accuracy? (precision, recall, F1, matriz de confusión).",
]:
    story.append(add_bullet(q))

story.append(Paragraph("Sobre explicabilidad (SHAP)", h2_style))
for q in [
    "¿Cómo funciona SHAP y por qué lo elegiste? (Valores de Shapley exactos para árboles con TreeExplainer).",
    "¿Qué diferencia hay entre SHAP global y local?",
    "¿Cómo le explicarías una predicción a alguien no técnico?",
]:
    story.append(add_bullet(q))

story.append(Paragraph("Sobre arquitectura y datos", h2_style))
for q in [
    "Recorreme la arquitectura de punta a punta.",
    "¿Cómo diseñas el esquema de base de datos? ¿Por qué PostgreSQL?",
    "¿Cómo procesas logs reales en streaming (miles/minuto) en vez de CSV? Aquí te preguntarán por Kafka/Flink, que tu proyecto NO tiene. Sé honesto: 'en esta versión es batch; para producción usaría Kafka'.",
]:
    story.append(add_bullet(q))

story.append(PageBreak())

story.append(Paragraph("Sobre producción / MLOps", h2_style))
for q in [
    "¿Qué pasa cuando el modelo se degrada en producción (model drift)? MUY común. Debes mencionar monitoreo de drift + reentrenamiento.",
    "¿Cómo versionas los modelos? (Tu proyecto usa aioplogmonitor_models_v0.1.0.pkl; ellos esperan MLflow/model registry).",
    "¿Qué monitoreas después del deploy? (latencia, errores, drift, volumen de predicciones).",
    "¿Cómo harías rollback de un modelo malo?",
    "¿Qué contiene tu pipeline CI/CD y por qué cada etapa?",
]:
    story.append(add_bullet(q))

story.append(Paragraph("Sobre seguridad", h2_style))
for q in [
    "¿Qué busca semgrep/gitleaks/trivy en tu repo?",
    "¿Cómo evitas inyección SQL al ingerir logs?",
]:
    story.append(add_bullet(q))

story.append(Paragraph("Preguntas de reflexión (las que más pesan)", h2_style))
for q in [
    "¿Qué harías diferente si lo rehicieras?",
    "¿Cuál fue el mayor riesgo o la parte más difícil?",
    "¿Qué dejaste fuera a propósito y por qué?",
]:
    story.append(add_bullet(q))
story.append(PageBreak())

# 4. Reclutadores
story.append(Paragraph("4. Preguntas que hacen los reclutadores (primera criba)", h1_style))
story.append(add_paragraph("Estas las hace RRHH o un recruiter sin perfil técnico. <b>No evalúan la matemática, evalúan propiedad, claridad y madurez.</b> Y lo más importante: qué señales de alerta (red flags) buscan."))
recruit_table = [
    [cell_header("Pregunta del reclutador"), cell_header("Qué evalúa"), cell_header("Red flag que debes evitar")],
    [cell("'Cuéntame un proyecto de IA/ML que hayas hecho y qué problema resolvía'"), cell("Si conectas tecnología con problema real"), cell("Empezar nombrando herramientas sin explicar por qué existía el proyecto")],
    [cell("'¿Qué parte hiciste tú personalmente?'"), cell("Propiedad real del trabajo"), cell("Decir solo 'hicimos' sin poder aislar tu aporte")],
    [cell("'¿Cuál fue el problema más difícil?'"), cell("Profundidad real"), cell("Decir 'ninguno' o culpar a los datos/compañeros")],
    [cell("'Si tuvieras un mes más, ¿qué cambiarías?'"), cell("Autoconciencia"), cell("Decir 'ya está completo, nada que mejorar'")],
    [cell("'¿Cómo supiste que tuvo éxito?'"), cell("Pensamiento más allá del modelo"), cell("Dar solo un 'accuracy = 1.0' sin contexto")],
    [cell("'Tu modelo da 95% de accuracy, ¿qué querrías saber?'"), cell("Conciencia de evaluación"), cell("Tratar el 95% como automáticamente excelente")],
    [cell("'¿Qué pasa después de desplegar un modelo?'"), cell("Mentalidad de producción"), cell("Decir 'el modelo ya no necesita atención'")],
    [cell("'Si el sistema empieza a dar peores resultados, ¿dónde mirarías primero?'"), cell("Troubleshooting sistemático"), cell("Reentrenar sin investigar la causa")],
    [cell("'Explícame una decisión técnica a alguien no técnico'"), cell("Comunicación"), cell("No poder explicar sin siglas")],
    [cell("'¿Qué riesgos revisarías antes de usar datos de clientes?'"), cell("IA responsable"), cell("Ignorar privacidad, sesgo, seguridad")],
]
table3 = Table(recruit_table, colWidths=[6*cm, 4.2*cm, 6*cm], repeatRows=1)
table3.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(table3)
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("<b>Cómo puntúan (scorecard típico 1-5):</b> propiedad del proyecto, entendimiento del problema, pensamiento de evaluación, conciencia de producción, comunicación y IA responsable. Necesitas ≥3 de media y ningún 1 para pasar a la ronda técnica.", quote_style))
story.append(PageBreak())

# 5. Cómo presentarlo
story.append(Paragraph("5. Cómo presentarlo: marco de 4-5 minutos", h1_style))
story.append(add_paragraph("Usa esta estructura pirámide invertida al decir 'háblame de tu proyecto':"))
presentation = [
    [cell_header("Etapa"), cell_header("Tiempo"), cell_header("Qué decir")],
    [cell("1. El gancho"), cell("30 seg"), cell("Las empresas gastan hasta 70% de su presupuesto IT en sistemas legacy que generan miles de logs por minuto, y los equipos pierden horas revisándolos a mano. Construí un sistema que los analiza automáticamente y prioriza los incidentes críticos.")],
    [cell("2. Tu enfoque"), cell("45 seg"), cell("Diseñé una arquitectura por capas: ingesta, almacenamiento en PostgreSQL, modelo de ML y una API REST. Mi rol fue... [di qué hiciste tú].")],
    [cell("3. Decisiones clave"), cell("60 seg"), cell("Elegí RandomForest + IsolationForest por interpretabilidad en vez de un autoencoder, porque en operaciones hay que justificar cada alerta. Añadí SHAP para que el modelo no sea caja negra.")],
    [cell("4. Detalles técnicos"), cell("60 seg"), cell("Solo lo interesante: desbalance de clases, features, cómo explicaste una predicción.")],
    [cell("5. Resultado + reflexión"), cell("45 seg"), cell("Métricas + 'lo que cambiaría: añadir detección de drift y streaming con Kafka para logs reales'.")],
]
table4 = Table(presentation, colWidths=[3.2*cm, 2*cm, 11*cm], repeatRows=1)
table4.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(table4)
story.append(PageBreak())

# 6. Consejos clave
story.append(Paragraph("6. Consejos clave para la entrevista", h1_style))
for tip in [
    "<b>Prepárate la pregunta del accuracy=1.0.</b> Es tu punto más vulnerable y el entrevistador lo va a oler. Ten una respuesta honesta: dataset pequeño/sintético, leakage posible, qué harías para validarlo bien.",
    "<b>Sé honesto sobre los límites.</b> Decir 'esto es batch, para producción usaría streaming + drift detection' te hace ver senior; decir que 'ya está perfecto' te hace ver junior.",
    "<b>Usa 'yo' y 'nosotros' con precisión.</b> Los entrevistadores detectan al instante a quien infla un trabajo en equipo.",
    "<b>Anticipa las 5 preguntas más probables:</b> accuracy=1.0, model drift, por qué RandomForest, cómo explicas una predicción con SHAP, y qué harías diferente.",
    "<b>Ten listo un ejemplo de decisión difícil:</b> por ejemplo, por qué elegiste ingeniería manual de features en vez de un autoencoder.",
]:
    story.append(add_bullet(tip))
story.append(PageBreak())

# 7. Plan de preparación
story.append(Paragraph("7. Plan de preparación recomendado", h1_style))
story.append(add_paragraph("Antes de la entrevista, dedica tiempo a:"))
prep = [
    [cell_header("Área"), cell_header("Qué hacer")],
    [cell("Proyecto"), cell("Leer README.md, docs/ARCHITECTURE.md y docs/LLD.md para tener todo claro.")],
    [cell("Modelo"), cell("Practicar explicar RandomForest vs IsolationForest, y cómo SHAP explica cada predicción.")],
    [cell("Límites"), cell("Preparar 2-3 formas de responder honestamente sobre batch vs streaming, y sobre accuracy=1.0.")],
    [cell("Historia"), cell("Practicar el marco de 4-5 minutos en voz alta (grabarte y revisar).")],
    [cell("Preguntas de RRHH"), cell("Responder sin tecnicismos las 10 preguntas de la Parte 4.")],
]
table5 = Table(prep, colWidths=[4.2*cm, 12*cm], repeatRows=1)
table5.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a237e')),
    ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#b0bec5')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#fafafa')]),
    ('TOPPADDING', (0,0), (-1,-1), 4),
    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ('LEFTPADDING', (0,0), (-1,-1), 5),
    ('RIGHTPADDING', (0,0), (-1,-1), 5),
]))
story.append(table5)

story.append(Spacer(1, 1*cm))
story.append(Paragraph("--- Fin del documento ---", ParagraphStyle('x', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor('#90a4ae'))))
story.append(Paragraph("Generado el 2026-11-14 | Proyecto AIOps Log Monitor", ParagraphStyle('x', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#b0bec5'))))

doc.build(story)
print(f"PDF generado en: {output_path}")