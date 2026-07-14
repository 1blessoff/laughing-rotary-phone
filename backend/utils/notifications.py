from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import os

User = get_user_model()

class NotificationService:
    """Service de gestion des notifications par email"""
    
    @staticmethod
    def envoyer_email(destinataire, sujet, message_html, message_plain=None, pieces_jointes=None):
        """
        Envoyer un email avec pièces jointes optionnelles
        """
        if not destinataire:
            return False
        
        try:
            if pieces_jointes:
                # Email avec pièces jointes
                email = EmailMessage(
                    subject=sujet,
                    body=message_plain or strip_tags(message_html),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[destinataire],
                )
                email.content_subtype = "html"
                
                for piece in pieces_jointes:
                    email.attach(piece['nom'], piece['contenu'], piece['mime_type'])
                
                email.send(fail_silently=False)
            else:
                # Email simple
                send_mail(
                    subject=sujet,
                    message=message_plain or strip_tags(message_html),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[destinataire],
                    html_message=message_html,
                    fail_silently=False,
                )
            return True
        except Exception as e:
            print(f"Erreur d'envoi d'email: {e}")
            return False
    
    @staticmethod
    def notification_nouvelle_reservation(reservation):
        """Notification à l'admin : nouvelle réservation"""
        sujet = f"Nouvelle réservation #{reservation.id}"
        message_html = f"""
        <h2>Nouvelle réservation</h2>
        <p>Une nouvelle réservation a été effectuée.</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Défunt</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.nom_defunt} {reservation.prenom_defunt}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Caveau</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.caveau.reference}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Date d'enterrement</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.date_enterrement}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Client</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.client.username}</td></tr>
        </table>
        <br>
        <a href="{settings.SITE_URL}/admin/reservations/reservation/{reservation.id}/change/">
            Voir la réservation dans l'administration
        </a>
        """
        admins = User.objects.filter(role='admin')
        for admin in admins:
            NotificationService.envoyer_email(
                destinataire=admin.email,
                sujet=sujet,
                message_html=message_html
            )
    
    @staticmethod
    def notification_reservation_validee(reservation):
        """Notification au client : réservation validée"""
        sujet = f"Réservation #{reservation.id} validée"
        message_html = f"""
        <h2>Réservation validée</h2>
        <p>Bonjour {reservation.client.username},</p>
        <p>Votre réservation pour le caveau <strong>{reservation.caveau.reference}</strong> a été validée.</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Défunt</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.nom_defunt} {reservation.prenom_defunt}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Date d'enterrement</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{reservation.date_enterrement}</td></tr>
        </table>
        <br>
        <p>Vous recevrez prochainement votre facture par email.</p>
        """
        NotificationService.envoyer_email(
            destinataire=reservation.client.email,
            sujet=sujet,
            message_html=message_html
        )
    
    @staticmethod
    def notification_reservation_refusee(reservation, motif):
        """Notification au client : réservation refusée"""
        sujet = f"Réservation #{reservation.id} refusée"
        message_html = f"""
        <h2>Réservation refusée</h2>
        <p>Bonjour {reservation.client.username},</p>
        <p>Votre réservation pour le caveau <strong>{reservation.caveau.reference}</strong> a été refusée.</p>
        <p><strong>Motif :</strong> {motif}</p>
        <p>Veuillez contacter l'administration pour plus d'informations.</p>
        """
        NotificationService.envoyer_email(
            destinataire=reservation.client.email,
            sujet=sujet,
            message_html=message_html
        )
    
    @staticmethod
    def notification_concession_creee(concession):
        """Notification au client : concession créée"""
        sujet = f"Concession créée - {concession.numero_contrat}"
        message_html = f"""
        <h2>Concession créée</h2>
        <p>Bonjour {concession.reservation.client.username},</p>
        <p>Une concession a été créée pour la réservation de <strong>{concession.reservation.nom_defunt}</strong>.</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Numéro de contrat</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.numero_contrat}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Type</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.type_concession}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Date de début</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.date_debut}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Date de fin</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.date_fin or 'Perpétuelle'}</td></tr>
        </table>
        <br>
        <p>Vous trouverez votre contrat de concession en pièce jointe.</p>
        """
        pieces = []
        if concession.contrat_pdf:
            pieces.append({
                'nom': f"contrat_{concession.numero_contrat}.pdf",
                'contenu': concession.contrat_pdf.read(),
                'mime_type': 'application/pdf'
            })

        NotificationService.envoyer_email(
            destinataire=concession.reservation.client.email,
            sujet=sujet,
            message_html=message_html,
            pieces_jointes=pieces if pieces else None
        )
    
    @staticmethod
    def notification_paiement_valide(paiement):
        """Notification au client : paiement validé"""
        sujet = f"Paiement validé - {paiement.reference_transaction}"
        message_html = f"""
        <h2> Paiement validé</h2>
        <p>Bonjour {paiement.reservation.client.username},</p>
        <p>Votre paiement a été validé.</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Référence</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paiement.reference_transaction}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Montant</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paiement.montant} FCFA</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Méthode</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{paiement.get_methode_display()}</td></tr>
        </table>
        <br>
        <p>Vous trouverez votre facture en pièce jointe.</p>
        """
        pieces = []
        if paiement.facture_pdf:
            pieces.append({
                'nom': f"facture_{paiement.reference_transaction}.pdf",
                'contenu': paiement.facture_pdf.read(),
                'mime_type': 'application/pdf'
            })
        
        NotificationService.envoyer_email(
            destinataire=paiement.reservation.client.email,
            sujet=sujet,
            message_html=message_html,
            pieces_jointes=pieces if pieces else None
        )
    
    @staticmethod
    def notification_concession_expiration(concession, jours_restants):
        """Notification : concession va expirer"""
        sujet = f"Concession {concession.numero_contrat} - Expiration dans {jours_restants} jours"
        message_html = f"""
        <h2> Expiration de concession</h2>
        <p>La concession <strong>{concession.numero_contrat}</strong> expire dans <strong>{jours_restants} jours</strong>.</p>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Défunt</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.reservation.nom_defunt}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Date d'expiration</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.date_fin}</td></tr>
            <tr><th style="border: 1px solid #ddd; padding: 8px;">Client</th>
                <td style="border: 1px solid #ddd; padding: 8px;">{concession.reservation.client.username}</td></tr>
        </table>
        <br>
        <p>Veuillez prendre les dispositions nécessaires pour le renouvellement.</p>
        """
        # Envoyer au client
        NotificationService.envoyer_email(
            destinataire=concession.reservation.client.email,
            sujet=sujet,
            message_html=message_html
        )
        # Envoyer à l'admin
        admins = User.objects.filter(role='admin')
        for admin in admins:
            NotificationService.envoyer_email(
                destinataire=admin.email,
                sujet=sujet + " (Alerte Admin)",
                message_html=message_html
            )