param([Parameter(Mandatory)][string]$Divine)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot
$template = Get-ChildItem "$root/mod/Public/*/RootTemplates/*.lsx" -File
if (@($template).Count -ne 1) { throw "Expected one ring template" }
$output = Join-Path "$root/compiled" ($template.BaseName + '.lsf')
& $Divine -g bg3 -a convert-resource -s $template.FullName -d $output
if ($LASTEXITCODE -ne 0) { throw "LSLib failed to compile the ring" }
