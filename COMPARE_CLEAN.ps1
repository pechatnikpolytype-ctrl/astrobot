$ErrorActionPreference = "Continue"
$old = "$env:USERPROFILE\Desktop\AstroBot_clean"
$new = (Get-Location).Path

function Show-Tree($path, $title) {
    Write-Host "`n=== $title ===" -ForegroundColor Cyan
    Write-Host "Путь: $path"
    if (-not (Test-Path $path)) { Write-Host "  ПАПКИ НЕТ" -ForegroundColor Red; return }
    Get-ChildItem -Path $path -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\|\\\.git\\' } |
        Sort-Object FullName |
        ForEach-Object {
            $rel = $_.FullName.Substring($path.Length).TrimStart('\')
            Write-Host ("  {0,10} байт  {1}" -f $_.Length, $rel)
        }
}

Show-Tree $old "СТАРАЯ ПАПКА AstroBot_clean"
Show-Tree $new "НОВАЯ ПАПКА astrobot"

Write-Host "`n=== СРАВНЕНИЕ: чего нет в astrobot, но есть в AstroBot_clean ===" -ForegroundColor Yellow
$oldFiles = Get-ChildItem -Path $old -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\|\\\.git\\' } |
    ForEach-Object { $_.FullName.Substring($old.Length).TrimStart('\') }

$newFiles = Get-ChildItem -Path $new -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.venv\\|\\__pycache__\\|\\\.git\\' } |
    ForEach-Object { $_.FullName.Substring($new.Length).TrimStart('\') }

$missing = $oldFiles | Where-Object { $_ -notin $newFiles }
if ($missing) {
    foreach ($m in $missing) {
        $sz = (Get-Item (Join-Path $old $m)).Length
        Write-Host ("  НЕТ в astrobot: {0,10} байт  {1}" -f $sz, $m) -ForegroundColor Red
    }
} else {
    Write-Host "  Всё из старой папки уже есть в новой (по именам файлов)." -ForegroundColor Green
}

Write-Host "`n=== ГЛАВНЫЕ КАНДИДАТЫ В ТОЧКУ ВХОДА в AstroBot_clean ===" -ForegroundColor Yellow
@("tgbot1.py","main.py","bot.py","bot_prod.py","webhook_bot.py","config.py","loader.py","scheduler.py") | ForEach-Object {
    $p = Join-Path $old $_
    if (Test-Path $p) {
        Write-Host ("  ЕСТЬ  {0,-20} {1,8} байт" -f $_, (Get-Item $p).Length) -ForegroundColor Green
    } else {
        Write-Host ("  нет   {0}" -f $_) -ForegroundColor DarkGray
    }
}
