"""
core/email_backend.py

Backend SMTP personnalisé pour contourner les erreurs de vérification SSL
du type :

    [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
    Basic Constraints of CA cert not marked critical (_ssl.c:1028)

CAUSE RÉELLE :
Un antivirus (Avast, Kaspersky, ESET...) qui fait de l'inspection HTTPS
génère à la volée de faux certificats pour intercepter le trafic chiffré.
Ces certificats ont souvent une extension "Basic Constraints" non marquée
comme critique. OpenSSL 3.x (Python 3.10+) rejette désormais strictement
ce genre de certificat, alors que les anciennes versions l'acceptaient.

POURQUOI LE MONKEYPATCH GLOBAL DANS settings.py NE SUFFIT PAS :
`ssl._create_default_https_context = ssl._create_unverified_context`
ne change que le contexte SSL par défaut utilisé par des libs comme
urllib/requests. Depuis Django 4.2, `EmailBackend` construit SON PROPRE
contexte SSL via la cached_property `ssl_context`, indépendamment de ce
contexte par défaut. Il faut donc surcharger cette propriété précisément.

IMPORTANT :
Ce backend désactive la vérification du certificat du serveur SMTP.
Cela protège toujours le contenu du trafic contre l'écoute passive
(le canal reste chiffré), mais PAS contre une attaque active de type
Man-in-the-Middle. À n'utiliser qu'en développement, ou en dernier
recours en prod en attendant de corriger la source réelle du problème
(configurer l'antivirus pour exclure ce processus de l'inspection SSL).
"""

import ssl

from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.utils.functional import cached_property


class InsecureSMTPEmailBackend(DjangoSMTPBackend):
    """
    Identique au backend SMTP standard de Django, sauf que le contexte SSL
    utilisé pour STARTTLS ne vérifie ni le certificat ni le hostname.
    """

    @cached_property
    def ssl_context(self):
        if self.ssl_certfile or self.ssl_keyfile:
            context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLS_CLIENT)
            context.load_cert_chain(self.ssl_certfile, self.ssl_keyfile)
        else:
            context = ssl.create_default_context()

        # C'est ici, précisément, que se joue le contournement.
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context