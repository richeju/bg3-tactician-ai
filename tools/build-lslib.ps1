param([Parameter(Mandatory)][string]$Divine)
$ErrorActionPreference = 'Stop'
$Divine = (Resolve-Path $Divine).Path
$root = Split-Path $PSScriptRoot
$temp = New-TemporaryFile
Remove-Item $temp
$work = New-Item -ItemType Directory $temp.FullName
function Invoke-Divine($action, $source, $destination) {
    & $Divine -g bg3 -a $action -s $source -d $destination
    if ($LASTEXITCODE -ne 0) { throw "Divine failed: $action ($LASTEXITCODE)" }
}
try {
    $stage = Join-Path $work 'stage'
    Copy-Item "$root/mod" $stage -Recurse
    foreach ($xml in Get-ChildItem "$stage/Localization" -Recurse -Filter '*.xml') {
        Invoke-Divine 'convert-loca' $xml.FullName ([IO.Path]::ChangeExtension($xml.FullName, 'loca'))
        Remove-Item $xml.FullName
    }
    foreach ($lsx in Get-ChildItem "$stage/Public/TacticianAI/RootTemplates" -Filter '*.lsx') {
        Invoke-Divine 'convert-resource' $lsx.FullName ([IO.Path]::ChangeExtension($lsx.FullName, 'lsf'))
        Remove-Item $lsx.FullName
    }
    $pak = Join-Path $work 'TacticianAI.pak'
    Invoke-Divine 'create-package' $stage $pak
    $verify = Join-Path $work 'verify'
    Invoke-Divine 'extract-package' $pak $verify
    foreach ($file in Get-ChildItem $stage -Recurse -File) {
        $name = [IO.Path]::GetRelativePath($stage, $file.FullName)
        if ((Get-FileHash $file.FullName).Hash -ne (Get-FileHash (Join-Path $verify $name)).Hash) {
            throw "Round-trip mismatch: $name"
        }
    }
    New-Item -ItemType Directory -Force "$root/dist" | Out-Null
    Copy-Item $pak "$root/dist/TacticianAI.pak" -Force
} finally {
    Remove-Item -LiteralPath $work.FullName -Recurse -Force
}
