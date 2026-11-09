param([string]$Work)
# Keeps Windows from sleeping while OpenDroneMap runs, and logs every line to run_log.txt (plain text).
$sig = '[DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint esFlags);'
$k = Add-Type -MemberDefinition $sig -Name Awake -Namespace Win32 -PassThru
[void]$k::SetThreadExecutionState([uint32]2147483649)   # continuous + system required: no idle sleep
$log = Join-Path $Work 'run_log.txt'
Set-Content -Path $log -Value ("Started " + (Get-Date))
$n = (Get-ChildItem (Join-Path $Work 'images') -Filter *.JPG).Count
Add-Content -Path $log -Value ("Photos: " + $n)
Write-Host ("Stitching " + $n + " photos. This window shows progress; it will take a few hours.")
docker run --rm -v "${Work}:/datasets/code" opendronemap/odm --project-path /datasets --dsm --dem-resolution 10 --orthophoto-resolution 5 --boundary /datasets/code/boundary.geojson --auto-boundary-distance 0 --pc-quality medium --feature-quality high --skip-3dmodel 2>&1 | ForEach-Object { $s = "$_"; Write-Host $s; Add-Content -Path $log -Value $s }
Add-Content -Path $log -Value ("Finished " + (Get-Date) + " exit code " + $LASTEXITCODE)
[void]$k::SetThreadExecutionState([uint32]2147483648)
