# find Documents folder location (usually $env:USERPROFILE\Documents)
$documents_folder = [environment]::GetFolderPath("MyDocuments")

# find Program Files (x86) folder location - Usually C:\Program Files (x86)
$prog_files_x86_folder = [environment]::GetFolderPath("ProgramFilesX86")

# try to find vswhere
$vswhere_path = "$prog_files_x86_folder\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not(Test-Path -Path $vswhere_path -PathType Leaf)) {
    $vs_installer_reg_key = "Registry::HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{6F320B93-EE3C-4826-85E0-ADF79F8D4C61}"
    $install_location = (Get-ItemProperty -Path $vs_installer_reg_key).InstallLocation.Trim('"')
    $vswhere_path = "$install_location\vswhere.exe"
    if (-not(Test-Path -Path $vswhere_path -PathType Leaf)) {
        $vswhere_path = $null
    }
}

if ($vswhere_path -ne $null) {
    # use vswhere to get list of installed visual studio versions
    $vs_versions = & $vswhere_path -property catalog_productLineVersion
    $vs_settings_folders = $vs_versions | ForEach-Object { "$documents_folder\Visual Studio $_" }
}
else {
    $vs_settings_folders = @()
}

# Add in existing "My Documents\Visual Studio XXXX" - perhaps these were uninstalled, or installed on a different
# machine and the profile is synced, or perhaps we just couldn't locate vswhere
$folder_names = Get-ChildItem -Path "$documents_folder" -Filter "Visual Studio *" | ForEach-Object { $_.Name }
$vs_settings_folders += ($folder_names | ForEach-Object { "$documents_folder\$_" })

# eliminate duplicates
$vs_settings_folders = $vs_settings_folders | Sort-Object | Get-Unique

$this_script = $MyInvocation.MyCommand.Path
$this_folder = [System.IO.Path]::GetDirectoryName($this_script)

foreach ($settings_folder in $vs_settings_folders) {
    $visualizer_folder = "$settings_folder\Visualizers"
    Write-Host "Installing USD .natvis Visualizers to: $visualizer_folder"
    New-Item -Type Directory -Force $visualizer_folder | Out-Null
    Copy-Item "$this_folder\*.natvis" -Destination $visualizer_folder
}