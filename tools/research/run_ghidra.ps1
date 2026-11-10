param([Parameter(Mandatory)][string]$Ghidra,[Parameter(Mandatory)][string]$Jdk,[Parameter(Mandatory)][string]$ProjectDirectory,[string]$Project='CH2K8Research',[string]$Script='XboxFieldAudit.java',[string]$Output='output/research/xbox-audit.txt',[string]$Candidates)
$ErrorActionPreference='Stop'
$studioRoot=(Resolve-Path "$PSScriptRoot/../..").Path
$projectPath=(Resolve-Path -LiteralPath $ProjectDirectory).Path
$outputPath=[IO.Path]::GetFullPath((Join-Path $studioRoot $Output))
New-Item -ItemType Directory -Force (Split-Path $outputPath) | Out-Null
$env:JAVA_HOME=(Resolve-Path -LiteralPath $Jdk).Path
$env:JAVA_TOOL_OPTIONS="-Dapplication.settingsdir=`"$studioRoot/output/ghidra-settings`" -Dapplication.cachedir=`"$studioRoot/output/ghidra-cache`""
$scriptArguments=@($outputPath)
if ($Candidates) {$scriptArguments+=(Resolve-Path -LiteralPath $Candidates).Path}
& "$Ghidra/support/analyzeHeadless.bat" $projectPath $Project -readOnly -process '*' -noanalysis -scriptPath $PSScriptRoot -postScript $Script @scriptArguments
if ($LASTEXITCODE) {throw "Ghidra failed ($LASTEXITCODE)"}
