# SMTP-Umstellung bei IONOS

1. Bisherige contact.php lokal als Sicherung herunterladen.
2. Nur die für unsere Maildiagnose angelegte php.ini entfernen. Bei anderweitig genutzter php.ini nur die Diagnosezeile sendmail_path entfernen. Ordner mail-diagnose samt Protokollen löschen.
3. Im Webspace-Hauptverzeichnis / einen neuen Ordner nebukad-private anlegen (NEBEN nebukad-international, nicht darin). Keine Domain auf diesen privaten Ordner verbinden.
4. smtp-password.php aus dem Paket in einem Texteditor öffnen. Nur HIER_POSTFACHPASSWORT_EINTRAGEN durch das Passwort von info@nebukad-international.com ersetzen. Keine zusätzlichen Anführungszeichen. UTF-8 ohne BOM speichern. Die Begrenzungszeile NEBUKAD_SMTP_PASSWORD_END; bleibt unverändert.
5. Die bearbeitete smtp-password.php nach /nebukad-private hochladen. Diese Datei niemals in GitHub, Chat oder Screenshots veröffentlichen.
6. Unter /nebukad-international den Ordner mail-lib erstellen. Alle sechs enthaltenen Dateien einzeln dort hochladen (Webspace Explorer überträgt Ordner nicht rekursiv).
7. contact.php nach /nebukad-international hochladen und die bisherige Datei ersetzen.
8. Kontaktseite neu laden, einmal absenden und den Empfang im Postfach einschließlich Spamordner prüfen.

Verbindung: smtp.ionos.de, Port 465, implizites TLS mit Zertifikatsprüfung, SMTP-Anmeldung mit vollständiger Postfachadresse. From und Empfänger sind fest eingestellt. Besucheradresse ausschließlich Reply-To. PHP 8.x mit OpenSSL verwenden. Keine zusätzlichen kostenpflichtigen Dienste nötig.

Die Oberfläche bleibt unverändert. Honeypot, Eingabeprüfung und Limits bleiben aktiv (5 Versuche pro IP/Stunde, 60 insgesamt). Fehlgeschlagene Versuche zählen ebenfalls. Bei HTTP 429 später erneut testen.

Diagnose im Browser-Netzwerk: smtp_config = Passwortdatei fehlt oder Platzhalter unverändert; smtp_failed = Bibliotheks-/Verbindungs-/Anmelde-/Versandfehler, noch kein Zustellnachweis; accepted = SMTP-Server hat die Nachricht angenommen, tatsächlichen Empfang separat prüfen. Passwort oder SMTP-Protokoll nicht offenlegen.

Kein produktiver Versand wurde vorab getestet, da das Postfachpasswort ausschließlich beim Betreiber bleibt.
