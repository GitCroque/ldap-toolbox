# Guide: Ajouter un Nouveau Reporter

## Introduction

Ce guide vous accompagne pour créer un nouveau format de reporter dans LDAP Health Monitor. Nous allons créer un **PDFReporter** comme exemple pratique qui génère des rapports d'audit au format PDF professionnel.

## Vue d'Ensemble

### Objectif

Créer un module `PDFReporter` qui:
- Génère des rapports PDF formatés professionnellement
- Inclut des graphiques et statistiques
- Supporte health checks et audit reports
- Est facilement configurable

### Architecture

```
Nouveau Reporter: src/reporters/pdf.py
│
├─> Utilise: reportlab (bibliothèque PDF)
├─> Utilise: matplotlib (graphiques)
├─> Input: HealthCheckResult, AuditReport
├─> Output: Fichier PDF
│
└─> Intégré dans: CLI (--format pdf)
```

## Étape 1: Installation des Dépendances

### 1.1 Ajouter aux Requirements

Ajoutez dans `requirements.txt`:

```text
# Existing dependencies...
reportlab>=4.0.0
matplotlib>=3.7.0
Pillow>=10.0.0
```

### 1.2 Installer

```bash
pip install reportlab matplotlib Pillow
```

## Étape 2: Créer le Module Reporter

### 2.1 Créer pdf.py

Créez `/home/user/ldap-toolbox/src/reporters/pdf.py`:

```python
"""Reporter pour génération de rapports PDF."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional

import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from src.core.models import HealthCheckResult, AuditReport, AuditIssue, AlertLevel


class PDFReporter:
    """Générateur de rapports PDF professionnels."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialise le reporter PDF.

        Args:
            config: Configuration optionnelle du reporter
        """
        self.config = config or {}
        self.pagesize = A4 if self.config.get("pagesize") == "A4" else letter
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Configure les styles personnalisés."""
        # Style pour le titre principal
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1a73e8"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        # Style pour les titres de section
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#34a853"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        # Style pour le texte d'issue critique
        self.styles.add(
            ParagraphStyle(
                name="CriticalIssue",
                parent=self.styles["Normal"],
                textColor=colors.red,
                fontSize=11,
            )
        )

    def export_health(self, health: HealthCheckResult, output_path: str) -> None:
        """Exporte un health check en PDF.

        Args:
            health: Résultat du health check
            output_path: Chemin du fichier PDF à créer
        """
        # Créer le document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Construire le contenu
        story = []

        # En-tête
        story.extend(self._build_header("LDAP Health Check Report"))

        # Informations générales
        story.extend(self._build_health_summary(health))

        # Statistiques
        if "statistics" in health.details:
            story.extend(self._build_statistics_section(health.details["statistics"]))

        # Graphique de santé
        chart = self._create_health_chart(health)
        if chart:
            story.append(chart)
            story.append(Spacer(1, 0.2 * inch))

        # Issues si présentes
        if "issues" in health.details and health.details["issues"]:
            story.extend(self._build_issues_section(health.details["issues"]))

        # Générer le PDF
        doc.build(story)

    def export_audit(self, report: AuditReport, output_path: str) -> None:
        """Exporte un rapport d'audit complet en PDF.

        Args:
            report: Rapport d'audit complet
            output_path: Chemin du fichier PDF à créer
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        # En-tête
        story.extend(self._build_header("LDAP Audit Report"))

        # Résumé exécutif
        story.extend(self._build_audit_summary(report))

        # Graphiques
        charts = self._create_audit_charts(report)
        for chart in charts:
            story.append(chart)
            story.append(Spacer(1, 0.2 * inch))

        # Health check
        if report.health:
            story.append(PageBreak())
            story.append(Paragraph("Health Check Details", self.styles["SectionTitle"]))
            story.extend(self._build_health_summary(report.health))

        # Issues par catégorie
        story.append(PageBreak())
        story.extend(self._build_issues_by_category(report.issues))

        # Recommandations
        if report.recommendations:
            story.append(PageBreak())
            story.extend(self._build_recommendations_section(report.recommendations))

        # Générer le PDF
        doc.build(story)

    def _build_header(self, title: str) -> List:
        """Construit l'en-tête du rapport.

        Args:
            title: Titre du rapport

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        # Titre
        elements.append(Paragraph(title, self.styles["CustomTitle"]))

        # Date de génération
        date_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        date_style = ParagraphStyle(
            name="DateStyle",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_RIGHT,
        )
        elements.append(Paragraph(date_text, date_style))
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _build_health_summary(self, health: HealthCheckResult) -> List:
        """Construit la section de résumé de santé.

        Args:
            health: Résultat du health check

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        elements.append(Paragraph("Health Summary", self.styles["SectionTitle"]))

        # Tableau de résumé
        data = [
            ["Status", str(health.status.value).upper()],
            ["Response Time", f"{health.response_time:.2f} ms"],
            ["Message", health.message],
            ["Timestamp", health.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
        ]

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _build_audit_summary(self, report: AuditReport) -> List:
        """Construit le résumé exécutif de l'audit.

        Args:
            report: Rapport d'audit

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        elements.append(Paragraph("Executive Summary", self.styles["SectionTitle"]))

        # Compter les issues par niveau
        critical = len([i for i in report.issues if i.level == AlertLevel.CRITICAL])
        warning = len([i for i in report.issues if i.level == AlertLevel.WARNING])
        info = len([i for i in report.issues if i.level == AlertLevel.INFO])

        # Tableau de résumé
        data = [
            ["Report Date", report.timestamp.strftime("%Y-%m-%d %H:%M:%S")],
            ["Health Score", f"{report.score}/100"],
            ["Total Issues", str(len(report.issues))],
            ["Critical Issues", str(critical)],
            ["Warnings", str(warning)],
            ["Informational", str(info)],
        ]

        # Ajouter statistiques si disponibles
        if report.statistics:
            if "users_total" in report.statistics:
                data.append(["Total Users", str(report.statistics["users_total"])])
            if "groups_total" in report.statistics:
                data.append(["Total Groups", str(report.statistics["groups_total"])])

        table = Table(data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightblue),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 0.3 * inch))

        return elements

    def _build_statistics_section(self, statistics: Dict[str, Any]) -> List:
        """Construit la section de statistiques.

        Args:
            statistics: Dictionnaire de statistiques

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        elements.append(Paragraph("Statistics", self.styles["SectionTitle"]))

        # Convertir en tableau
        data = [["Metric", "Value"]]
        for key, value in statistics.items():
            if isinstance(value, (int, float)):
                data.append([key.replace("_", " ").title(), str(value)])

        if len(data) > 1:
            table = Table(data, colWidths=[3 * inch, 3 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ]
                )
            )

            elements.append(table)
            elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _build_issues_section(self, issues: List[Dict[str, Any]]) -> List:
        """Construit la section des issues.

        Args:
            issues: Liste des issues

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        elements.append(Paragraph("Issues Found", self.styles["SectionTitle"]))

        for issue in issues:
            level = issue.get("level", "info")
            title = issue.get("title", "")
            description = issue.get("description", "")
            recommendation = issue.get("recommendation", "")

            # Couleur selon le niveau
            if level == "critical":
                style = self.styles["CriticalIssue"]
            elif level == "warning":
                style = ParagraphStyle(
                    name="WarningIssue",
                    parent=self.styles["Normal"],
                    textColor=colors.orange,
                )
            else:
                style = self.styles["Normal"]

            # Titre de l'issue
            issue_title = f"<b>{level.upper()}:</b> {title}"
            elements.append(Paragraph(issue_title, style))

            # Description
            elements.append(Paragraph(description, self.styles["Normal"]))

            # Recommandation
            if recommendation:
                rec_text = f"<i>Recommendation: {recommendation}</i>"
                elements.append(Paragraph(rec_text, self.styles["Normal"]))

            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _build_issues_by_category(self, issues: List[AuditIssue]) -> List:
        """Construit les issues groupées par catégorie.

        Args:
            issues: Liste des issues

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        # Grouper par catégorie
        by_category: Dict[str, List[AuditIssue]] = {}
        for issue in issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)

        # Créer une section par catégorie
        for category, category_issues in sorted(by_category.items()):
            elements.append(
                Paragraph(
                    f"{category.title()} Issues ({len(category_issues)})",
                    self.styles["SectionTitle"],
                )
            )

            for issue in category_issues:
                # Icône selon le niveau
                level_icon = {
                    AlertLevel.CRITICAL: "🔴",
                    AlertLevel.WARNING: "⚠️",
                    AlertLevel.INFO: "ℹ️",
                }.get(issue.level, "")

                # Titre
                title_text = f"{level_icon} <b>{issue.title}</b>"
                elements.append(Paragraph(title_text, self.styles["Normal"]))

                # Description
                elements.append(Paragraph(issue.description, self.styles["Normal"]))

                # DN affecté
                if issue.affected_dn:
                    dn_text = f"<i>Affected: {issue.affected_dn}</i>"
                    elements.append(Paragraph(dn_text, self.styles["Normal"]))

                # Recommandation
                if issue.recommendation:
                    rec_text = f"💡 <i>{issue.recommendation}</i>"
                    elements.append(Paragraph(rec_text, self.styles["Normal"]))

                elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _build_recommendations_section(self, recommendations: List[str]) -> List:
        """Construit la section des recommandations.

        Args:
            recommendations: Liste des recommandations

        Returns:
            Liste d'éléments reportlab
        """
        elements = []

        elements.append(Paragraph("Recommendations", self.styles["SectionTitle"]))

        for i, rec in enumerate(recommendations, 1):
            rec_text = f"{i}. {rec}"
            elements.append(Paragraph(rec_text, self.styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _create_health_chart(self, health: HealthCheckResult) -> Optional[Image]:
        """Crée un graphique de santé.

        Args:
            health: Résultat du health check

        Returns:
            Image reportlab ou None
        """
        try:
            # Créer un graphique simple
            fig, ax = plt.subplots(figsize=(6, 4))

            # Données pour le graphique
            response_time = health.response_time
            threshold_warning = 500
            threshold_critical = 2000

            # Graphique en barres
            categories = ["Current", "Warning\nThreshold", "Critical\nThreshold"]
            values = [response_time, threshold_warning, threshold_critical]
            colors_list = ["green" if response_time < threshold_warning else "orange", "orange", "red"]

            ax.bar(categories, values, color=colors_list)
            ax.set_ylabel("Response Time (ms)")
            ax.set_title("LDAP Response Time Analysis")
            ax.axhline(y=threshold_warning, color="orange", linestyle="--", label="Warning")
            ax.axhline(y=threshold_critical, color="red", linestyle="--", label="Critical")
            ax.legend()

            # Sauvegarder dans un buffer
            buf = BytesIO()
            plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
            buf.seek(0)
            plt.close(fig)

            # Créer l'image reportlab
            img = Image(buf, width=5 * inch, height=3.33 * inch)
            return img

        except Exception as e:
            # Si erreur, retourner None
            print(f"Warning: Could not create chart: {e}")
            return None

    def _create_audit_charts(self, report: AuditReport) -> List[Image]:
        """Crée les graphiques pour le rapport d'audit.

        Args:
            report: Rapport d'audit

        Returns:
            Liste d'images reportlab
        """
        charts = []

        # Graphique 1: Distribution des issues par niveau
        try:
            chart = self._create_issues_distribution_chart(report.issues)
            if chart:
                charts.append(chart)
        except Exception as e:
            print(f"Warning: Could not create issues chart: {e}")

        # Graphique 2: Distribution par catégorie
        try:
            chart = self._create_category_distribution_chart(report.issues)
            if chart:
                charts.append(chart)
        except Exception as e:
            print(f"Warning: Could not create category chart: {e}")

        return charts

    def _create_issues_distribution_chart(self, issues: List[AuditIssue]) -> Optional[Image]:
        """Crée un graphique de distribution des issues par niveau.

        Args:
            issues: Liste des issues

        Returns:
            Image reportlab ou None
        """
        if not issues:
            return None

        # Compter par niveau
        counts = {
            "Critical": len([i for i in issues if i.level == AlertLevel.CRITICAL]),
            "Warning": len([i for i in issues if i.level == AlertLevel.WARNING]),
            "Info": len([i for i in issues if i.level == AlertLevel.INFO]),
        }

        # Créer le graphique
        fig, ax = plt.subplots(figsize=(6, 4))
        colors_list = ["red", "orange", "blue"]

        ax.bar(counts.keys(), counts.values(), color=colors_list)
        ax.set_ylabel("Number of Issues")
        ax.set_title("Issues Distribution by Severity")

        # Ajouter les valeurs sur les barres
        for i, (key, value) in enumerate(counts.items()):
            ax.text(i, value, str(value), ha="center", va="bottom")

        # Sauvegarder
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return Image(buf, width=5 * inch, height=3.33 * inch)

    def _create_category_distribution_chart(self, issues: List[AuditIssue]) -> Optional[Image]:
        """Crée un graphique de distribution par catégorie.

        Args:
            issues: Liste des issues

        Returns:
            Image reportlab ou None
        """
        if not issues:
            return None

        # Compter par catégorie
        category_counts: Dict[str, int] = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1

        # Créer le graphique (pie chart)
        fig, ax = plt.subplots(figsize=(6, 4))

        ax.pie(
            category_counts.values(),
            labels=category_counts.keys(),
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title("Issues Distribution by Category")

        # Sauvegarder
        buf = BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)

        return Image(buf, width=5 * inch, height=3.33 * inch)
```

### 2.2 Points Clés du Code

**Architecture:**
- Utilise reportlab pour la génération PDF
- Utilise matplotlib pour les graphiques
- Supporte personnalisation via config

**Méthodes principales:**
- `export_health()`: Exporte un health check
- `export_audit()`: Exporte un rapport d'audit complet

**Fonctionnalités:**
- Styles personnalisés (couleurs, polices)
- Tableaux formatés
- Graphiques intégrés
- Multi-pages
- Groupement par catégorie

## Étape 3: Intégration CLI

### 3.1 Importer le Module

Dans `src/cli.py`:

```python
# Avec les autres imports de reporters
from src.reporters.pdf import PDFReporter
```

### 3.2 Ajouter PDF au Choix de Format

```python
@audit.command("all")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["console", "json", "html", "pdf"]),  # ← Ajouter "pdf"
    default="console"
)
@click.pass_context
def audit_all(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Run all audit checks."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)

        # ... exécuter les audits ...

        # Output report
        if format == "console":
            reporter = ConsoleReporter()
            reporter.report_audit(report)
        elif format == "json":
            if not output:
                output = "audit_report.json"
            reporter = JSONReporter()
            reporter.export_audit(report, output)
            click.echo(f"✅ Report saved to {output}")
        elif format == "html":
            if not output:
                output = "audit_report.html"
            reporter = HTMLReporter()
            reporter.export_audit(report, output)
            click.echo(f"✅ Report saved to {output}")
        elif format == "pdf":  # ← NOUVEAU
            if not output:
                output = "audit_report.pdf"
            reporter = PDFReporter()
            reporter.export_audit(report, output)
            click.echo(f"✅ PDF report saved to {output}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
```

### 3.3 Ajouter au Health Check

```python
@audit.command("health")
@click.option("--output", "-o", help="Output file path")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["console", "json", "html", "pdf"]),  # ← Ajouter "pdf"
    default="console"
)
@click.pass_context
def audit_health(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Check LDAP server health."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        checker = HealthChecker(connector, config)

        health = checker.check_health()

        if format == "console":
            reporter = ConsoleReporter()
            reporter.report_health(health)
        elif format == "json":
            if not output:
                output = "health_report.json"
            reporter = JSONReporter()
            reporter.export_health(health, output)
            click.echo(f"✅ Report saved to {output}")
        elif format == "pdf":  # ← NOUVEAU
            if not output:
                output = "health_report.pdf"
            reporter = PDFReporter()
            reporter.export_health(health, output)
            click.echo(f"✅ PDF report saved to {output}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
```

### 3.4 Mettre à Jour __init__.py

Dans `src/reporters/__init__.py`:

```python
"""Modules de reporting."""

from src.reporters.console import ConsoleReporter
from src.reporters.csv import CSVReporter
from src.reporters.html import HTMLReporter
from src.reporters.json import JSONReporter
from src.reporters.pdf import PDFReporter  # ← NOUVEAU
from src.reporters.prometheus import PrometheusReporter

__all__ = [
    "ConsoleReporter",
    "CSVReporter",
    "HTMLReporter",
    "JSONReporter",
    "PDFReporter",  # ← NOUVEAU
    "PrometheusReporter",
]
```

## Étape 4: Configuration (Optionnel)

### 4.1 Ajouter Configuration PDF

Dans `config.example.yaml`:

```yaml
reports:
  output_dir: "./reports"
  default_format: "html"
  include_graphs: true
  include_recommendations: true

  # Configuration PDF
  pdf:
    pagesize: "A4"  # ou "letter"
    logo_path: null  # Chemin vers logo (optionnel)
    company_name: "Your Company"
    show_charts: true
```

### 4.2 Utiliser la Configuration

Modifiez le PDFReporter pour utiliser la config:

```python
class PDFReporter:
    def __init__(self, config: Optional[Config] = None) -> None:
        """Initialise le reporter PDF.

        Args:
            config: Configuration complète de l'application
        """
        self.app_config = config
        pdf_config = config.reports.pdf if config else {}
        self.pagesize = A4 if pdf_config.get("pagesize") == "A4" else letter
        self.company_name = pdf_config.get("company_name", "")
        self.show_charts = pdf_config.get("show_charts", True)
        # ...
```

## Étape 5: Tests

### 5.1 Tests Unitaires

Créez `tests/unit/test_pdf_reporter.py`:

```python
"""Tests pour le PDFReporter."""

import pytest
from pathlib import Path
from datetime import datetime

from src.reporters.pdf import PDFReporter
from src.core.models import (
    HealthCheckResult,
    CheckStatus,
    AuditReport,
    AuditIssue,
    AlertLevel,
)


@pytest.fixture
def pdf_reporter():
    """Instance du PDFReporter."""
    return PDFReporter()


@pytest.fixture
def sample_health():
    """Health check de test."""
    return HealthCheckResult(
        status=CheckStatus.HEALTHY,
        response_time=150.5,
        message="Server is healthy",
        details={
            "statistics": {
                "users_total": 1000,
                "groups_total": 50,
            }
        },
    )


@pytest.fixture
def sample_audit_report():
    """Rapport d'audit de test."""
    issues = [
        AuditIssue(
            level=AlertLevel.WARNING,
            category="users",
            title="Inactive user",
            description="User inactive for 90 days",
            recommendation="Review account",
        ),
        AuditIssue(
            level=AlertLevel.CRITICAL,
            category="security",
            title="Weak password",
            description="User has weak password",
            recommendation="Enforce password policy",
        ),
    ]

    return AuditReport(
        timestamp=datetime.now(),
        issues=issues,
        statistics={"users_total": 1000},
        score=85,
    )


class TestPDFReporter:
    """Tests pour PDFReporter."""

    def test_initialization(self, pdf_reporter):
        """Test initialisation."""
        assert pdf_reporter is not None
        assert pdf_reporter.styles is not None

    def test_export_health_creates_file(self, pdf_reporter, sample_health, tmp_path):
        """Test que export_health crée un fichier."""
        output_path = tmp_path / "health.pdf"

        pdf_reporter.export_health(sample_health, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_export_audit_creates_file(self, pdf_reporter, sample_audit_report, tmp_path):
        """Test que export_audit crée un fichier."""
        output_path = tmp_path / "audit.pdf"

        pdf_reporter.export_audit(sample_audit_report, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_build_header_returns_elements(self, pdf_reporter):
        """Test construction de l'en-tête."""
        elements = pdf_reporter._build_header("Test Report")

        assert len(elements) > 0

    def test_build_health_summary(self, pdf_reporter, sample_health):
        """Test construction du résumé de santé."""
        elements = pdf_reporter._build_health_summary(sample_health)

        assert len(elements) > 0

    def test_create_health_chart(self, pdf_reporter, sample_health):
        """Test création du graphique de santé."""
        chart = pdf_reporter._create_health_chart(sample_health)

        # Chart peut être None si matplotlib pas disponible
        assert chart is None or hasattr(chart, "drawOn")

    def test_build_issues_by_category(self, pdf_reporter, sample_audit_report):
        """Test construction des issues par catégorie."""
        elements = pdf_reporter._build_issues_by_category(sample_audit_report.issues)

        assert len(elements) > 0

    def test_create_issues_distribution_chart(self, pdf_reporter, sample_audit_report):
        """Test création graphique distribution."""
        chart = pdf_reporter._create_issues_distribution_chart(sample_audit_report.issues)

        assert chart is None or hasattr(chart, "drawOn")
```

### 5.2 Exécuter les Tests

```bash
# Tests unitaires
pytest tests/unit/test_pdf_reporter.py -v

# Avec couverture
pytest tests/unit/test_pdf_reporter.py --cov=src.reporters.pdf --cov-report=html

# Tous les tests reporters
pytest tests/unit/test_*_reporter.py -v
```

## Étape 6: Test Manuel

### 6.1 Générer un PDF de Test

```bash
# Health check en PDF
ldap-monitor audit health --format pdf -o health_test.pdf

# Audit complet en PDF
ldap-monitor audit all --format pdf -o audit_test.pdf

# Vérifier le fichier
ls -lh audit_test.pdf
open audit_test.pdf  # ou xdg-open sur Linux
```

### 6.2 Validation du PDF

Vérifiez que le PDF contient:
- [ ] En-tête avec titre et date
- [ ] Résumé exécutif
- [ ] Tableaux formatés
- [ ] Graphiques (si matplotlib disponible)
- [ ] Issues groupées par catégorie
- [ ] Recommandations
- [ ] Multi-pages si nécessaire

## Checklist Complète

- [ ] **Code**
  - [ ] Fichier `src/reporters/pdf.py` créé
  - [ ] Méthodes `export_health()` et `export_audit()` implémentées
  - [ ] Styles personnalisés configurés
  - [ ] Gestion d'erreurs robuste
  - [ ] Docstrings complètes

- [ ] **Dépendances**
  - [ ] reportlab ajouté à requirements.txt
  - [ ] matplotlib ajouté à requirements.txt
  - [ ] Dépendances installées

- [ ] **Intégration CLI**
  - [ ] Import ajouté dans cli.py
  - [ ] "pdf" ajouté aux choix de format
  - [ ] Intégré dans audit all
  - [ ] Intégré dans audit health
  - [ ] Ajouté dans __init__.py

- [ ] **Configuration**
  - [ ] Configuration PDF ajoutée à config.example.yaml
  - [ ] Configuration utilisée dans le reporter

- [ ] **Tests**
  - [ ] Tests unitaires créés
  - [ ] Tests passent avec succès
  - [ ] Couverture > 70%

- [ ] **Documentation**
  - [ ] Docstrings du module
  - [ ] Exemples d'utilisation
  - [ ] README mis à jour

- [ ] **Validation**
  - [ ] PDF généré avec succès
  - [ ] Contenu correct
  - [ ] Graphiques affichés
  - [ ] Pas de régression

## Bonnes Pratiques

### 1. Gestion d'Erreurs Gracieuse

```python
def _create_chart(self, data):
    """Crée un graphique, retourne None si erreur."""
    try:
        # Créer le graphique
        return chart
    except Exception as e:
        print(f"Warning: Could not create chart: {e}")
        return None  # Ne pas faire échouer le rapport entier
```

### 2. Configuration Flexible

```python
# Permettre désactivation des graphiques
if self.config.get("show_charts", True):
    charts = self._create_charts(report)
    story.extend(charts)
```

### 3. Style Réutilisable

```python
def _setup_custom_styles(self):
    """Centralise tous les styles personnalisés."""
    self.styles.add(ParagraphStyle(...))
```

### 4. Pagination Intelligente

```python
# Ajouter page break avant sections importantes
story.append(PageBreak())
story.append(Paragraph("New Section", ...))
```

## Conclusion

Vous avez maintenant créé un reporter PDF complet! Le même pattern peut être utilisé pour d'autres formats:

- **MarkdownReporter**: Génère Markdown
- **ExcelReporter**: Génère fichiers Excel
- **EmailReporter**: Envoie rapports par email
- **SlackReporter**: Poste dans Slack
- **XMLReporter**: Génère XML

Le système de reporters est complètement extensible!
