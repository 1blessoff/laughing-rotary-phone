from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime
import os
from django.conf import settings

class PDFGenerator:
    @staticmethod
    def generer_facture(paiement):
        """Generer une facture PDF pour un paiement"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Styles personnalises
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=24,
            textColor=colors.darkblue,
            spaceAfter=30
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontSize=14,
            textColor=colors.grey,
            spaceAfter=20
        )
        
        # Contenu
        story = []
        
        # En-tete
        story.append(Paragraph("GESTION FUNERAIRE", title_style))
        story.append(Paragraph("FACTURE", subtitle_style))
        story.append(Spacer(1, 20))
        
        # Informations de la facture
        reservation = paiement.reservation
        client = reservation.client
        
        info_data = [
            ["Numero de facture:", f"FACT-{paiement.id}-{datetime.now().year}"],
            ["Date:", datetime.now().strftime("%d/%m/%Y %H:%M")],
            ["Reference transaction:", paiement.reference_transaction],
            ["Client:", f"{client.username} ({client.email})"],
            ["Defunt:", f"{reservation.nom_defunt} {reservation.prenom_defunt}"],
            ["Caveau:", reservation.caveau.reference],
            ["Methode de paiement:", paiement.get_methode_display()],
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Details des paiements
        story.append(Paragraph("Details du paiement", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        paiement_data = [
            ["Description", "Montant"],
            [f"Concession - {reservation.nom_defunt}", f"{paiement.montant:,.0f} FCFA"],
        ]
        
        if paiement.est_partiel:
            paiement_data.append(["Solde restant", f"{paiement.solde_restant:,.0f} FCFA"])
        
        paiement_table = Table(paiement_data, colWidths=[4*inch, 3*inch])
        paiement_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(paiement_table)
        story.append(Spacer(1, 20))
        
        # Total
        total_data = [
            ["TOTAL", f"{paiement.montant:,.0f} FCFA"],
        ]
        total_table = Table(total_data, colWidths=[4*inch, 3*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(total_table)
        
        # Pied de page
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "Merci pour votre confiance. Ce document fait foi.",
            styles['Italic']
        ))
        
        # Generer le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def generer_contrat(concession):
        """Generer un contrat de concession PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # Styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            fontSize=24,
            textColor=colors.darkgreen,
            spaceAfter=30
        )
        
        # Contenu
        story = []
        
        reservation = concession.reservation
        client = reservation.client
        caveau = reservation.caveau
        
        # En-tete
        story.append(Paragraph("GESTION FUNERAIRE", title_style))
        story.append(Paragraph("CONTRAT DE CONCESSION", styles['Heading2']))
        story.append(Spacer(1, 20))
        
        # Informations du contrat
        info_data = [
            ["Numero de contrat:", concession.numero_contrat],
            ["Date:", datetime.now().strftime("%d/%m/%Y")],
            ["Type de concession:", concession.type_concession.capitalize()],
            ["Date de debut:", concession.date_debut.strftime("%d/%m/%Y")],
            ["Date de fin:", concession.date_fin.strftime("%d/%m/%Y") if concession.date_fin else "Perpetuelle"],
            ["Duree:", f"{concession.duree_ans} ans" if concession.type_concession != 'perpetuelle' else "Perpetuelle"],
        ]
        
        info_table = Table(info_data, colWidths=[3*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Informations du titulaire
        story.append(Paragraph("Informations du titulaire", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        titulaire_data = [
            ["Nom:", client.username],
            ["Email:", client.email],
            ["Telephone:", client.phone or "Non renseigne"],
        ]
        
        titulaire_table = Table(titulaire_data, colWidths=[2*inch, 5*inch])
        titulaire_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(titulaire_table)
        story.append(Spacer(1, 20))
        
        # Informations du defunt
        story.append(Paragraph("Informations du defunt", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        defunt_data = [
            ["Nom:", f"{reservation.nom_defunt} {reservation.prenom_defunt}"],
            ["Date de deces:", reservation.date_deces.strftime("%d/%m/%Y")],
            ["Date d'enterrement:", reservation.date_enterrement.strftime("%d/%m/%Y")],
            ["Caveau:", caveau.reference],
            ["Section:", caveau.section],
            ["Bloc:", caveau.bloc or "Non specifie"],
            ["Allee:", caveau.allee or "Non specifie"],
        ]
        
        defunt_table = Table(defunt_data, colWidths=[2*inch, 5*inch])
        defunt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(defunt_table)
        story.append(Spacer(1, 20))
        
        # Conditions generales
        story.append(Paragraph("Conditions generales", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        conditions = [
            "1. La presente concession est accordee pour une duree determinee.",
            "2. Le titulaire s'engage a respecter les reglements du cimetiere.",
            "3. Tout renouvellement doit etre demande avant la date d'expiration.",
            "4. Les travaux sur le caveau doivent etre autorises par l'administration.",
            "5. En cas de non-respect des conditions, la concession peut etre resolue.",
        ]
        
        for condition in conditions:
            story.append(Paragraph(condition, styles['Normal']))
            story.append(Spacer(1, 5))
        
        # Signatures
        story.append(Spacer(1, 30))
        story.append(Paragraph("Fait a Brazzaville, le " + datetime.now().strftime("%d/%m/%Y"), styles['Normal']))
        story.append(Spacer(1, 20))
        
        signature_data = [
            ["Le titulaire", "L'Administrateur"],
            ["", ""],
            ["Signature", "Signature"],
        ]
        
        signature_table = Table(signature_data, colWidths=[3.5*inch, 3.5*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 20),
        ]))
        story.append(signature_table)
        
        # Generer le PDF
        doc.build(story)
        buffer.seek(0)
        return buffer