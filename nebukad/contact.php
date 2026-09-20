<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
function respond(int $status, string $code): void {
    http_response_code($status);
    echo json_encode(['code' => $code]);
    exit;
}
if ($_SERVER['REQUEST_METHOD'] !== 'POST') respond(405, 'method');
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';
if (!in_array($origin, ['https://nebukad-international.com', 'https://www.nebukad-international.com'], true)) respond(403, 'origin');
if (($_SERVER['HTTP_X_NEBUKAD_FORM'] ?? '') !== '1') respond(403, 'origin');
if ((int)($_SERVER['CONTENT_LENGTH'] ?? 0) > 24000) respond(413, 'invalid');
$raw = file_get_contents('php://input', false, null, 0, 24001);
if ($raw === false || strlen($raw) > 24000) respond(413, 'invalid');
$data = json_decode($raw, true);
if (!is_array($data)) respond(400, 'invalid');
foreach (['name', 'email', 'message', 'website'] as $key) {
    if (!isset($data[$key]) || !is_string($data[$key])) respond(400, 'invalid');
}
if ($data['website'] !== '') respond(400, 'invalid');
$name = trim($data['name']);
$email = trim($data['email']);
$message = trim($data['message']);
if ($name === '' || strlen($name) > 400 || preg_match('/[\r\n\x00]/', $name)) respond(400, 'invalid');
if (strlen($email) > 254 || preg_match('/[\r\n\x00]/', $email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) respond(400, 'invalid');
if ($message === '' || strlen($message) > 20000 || strpos($message, "\0") !== false) respond(400, 'invalid');
// One bounded file outside the web root. Entries expire after one hour.
$ratePath = sys_get_temp_dir() . '/nebukad-contact-' . hash('sha256', __DIR__) . '.json';
$file = fopen($ratePath, 'c+');
if (!$file || !flock($file, LOCK_EX)) respond(503, 'unavailable');
chmod($ratePath, 0600);
$entries = json_decode(stream_get_contents($file), true);
if (!is_array($entries)) $entries = [];
$now = time();
$entries = array_values(array_filter($entries, static function ($entry) use ($now) {
    return is_array($entry) && isset($entry['time'], $entry['ip']) && $entry['time'] > $now - 3600;
}));
$ip = hash('sha256', __DIR__ . '|' . ($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
$own = array_filter($entries, static function ($entry) use ($ip) { return $entry['ip'] === $ip; });
if (count($entries) >= 60 || count($own) >= 5) {
    flock($file, LOCK_UN); fclose($file); respond(429, 'limit');
}
$entries[] = ['time' => $now, 'ip' => $ip];
rewind($file); ftruncate($file, 0);
$saved = fwrite($file, json_encode($entries));
fflush($file); flock($file, LOCK_UN); fclose($file);
if ($saved === false) respond(503, 'unavailable');
// Credentials live outside the domain's document root and are never committed.
try {
    $configPath = dirname(__DIR__) . '/nebukad-private/smtp-password.php';
    if (!is_file($configPath)) respond(503, 'smtp_config');
    $password = require $configPath;
    if (!is_string($password) || $password === '' || $password === 'HIER_POSTFACHPASSWORT_EINTRAGEN') {
        respond(503, 'smtp_config');
    }
    require_once __DIR__ . '/mail-lib/Exception.php';
    require_once __DIR__ . '/mail-lib/PHPMailer.php';
    require_once __DIR__ . '/mail-lib/SMTP.php';
    $mail = new \PHPMailer\PHPMailer\PHPMailer(true);
    $mail->isSMTP();
    $mail->Host = 'smtp.ionos.de';
    $mail->Port = 465;
    $mail->SMTPSecure = \PHPMailer\PHPMailer\PHPMailer::ENCRYPTION_SMTPS;
    $mail->SMTPAuth = true;
    $mail->Username = 'info@nebukad-international.com';
    $mail->Password = $password;
    $mail->SMTPDebug = 0;
    $mail->Timeout = 10;
    $mail->Timelimit = 10;
    $mail->CharSet = 'UTF-8';
    $mail->Encoding = 'base64';
    $mail->setFrom($mail->Username, 'Nebukad Website');
    $mail->addAddress($mail->Username);
    $mail->addReplyTo($email, $name);
    $mail->Subject = 'Nebukad Website - Kontakt / Contact';
    $mail->Body = "Name: $name\nE-Mail: $email\n\n$message";
    $mail->send();
    respond(200, 'accepted');
} catch (\Throwable $error) {
    // No SMTP transcript, credentials or visitor data in responses/logs.
    respond(503, 'smtp_failed');
}
