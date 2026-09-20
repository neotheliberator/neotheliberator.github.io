const form = document.querySelector('#contact-form');
if (form) {
  const de = document.documentElement.lang === 'de';
  const status = document.querySelector('#form-status');
  const button = form.querySelector('button');
  const live = ['nebukad-international.com', 'www.nebukad-international.com'].includes(location.hostname) && location.protocol === 'https:';
  const say = (a,b) => { status.textContent = de ? a : b; };
  if (!live) say('Vorschau: Der Formularversand wird mit dem Start der Website freigeschaltet.','Preview: Form submission will be enabled when the website launches.');
  else button.disabled = false;
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!live || button.disabled || !form.reportValidity()) return;
    button.disabled = true;
    say('Nachricht wird übermittelt …','Submitting message …');
    const data = Object.fromEntries(new FormData(form));
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch('contact.php', {method:'POST', headers:{'Content-Type':'application/json','X-Nebukad-Form':'1'}, body:JSON.stringify(data), signal:controller.signal});
      const result = await response.json();
      if (response.ok && result.code === 'accepted') {
        form.reset();
        say('Ihre Nachricht wurde zum Versand angenommen. Vielen Dank.','Your message has been accepted for sending. Thank you.');
      } else if (response.status === 429) {
        say('Zu viele Anfragen. Bitte versuchen Sie es später oder schreiben Sie uns per E-Mail.','Too many requests. Please try later or contact us by email.');
      } else throw new Error('submission');
    } catch {
      say('Der Versand konnte nicht bestätigt werden. Ihre Eingaben bleiben erhalten. Bitte versuchen Sie es später erneut.','Sending could not be confirmed. Your entries have been retained. Please try again later.');
    } finally { clearTimeout(timeout); button.disabled = false; }
  });
}
