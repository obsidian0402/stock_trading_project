# AI worklog 명령어를 어디서든 호출할 수 있도록 프로젝트 루트를 현재 사용자 PATH에 추가합니다.
# 시스템 전체가 아닌 "현재 사용자"의 환경변수에만 영향을 주므로 관리자 권한이 필요 없습니다.
#
# 사용:
#   .\scripts\install_ai_path.ps1            # 추가
#   .\scripts\install_ai_path.ps1 -Remove    # 제거

[CmdletBinding()]
param(
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$current = [Environment]::GetEnvironmentVariable("Path", "User")
if ($null -eq $current) { $current = "" }
$entries = $current -split ";" | Where-Object { $_ -ne "" }

if ($Remove) {
    if ($entries -notcontains $projectRoot) {
        Write-Host "PATH에 '$projectRoot' 가 등록되어 있지 않습니다. 변경 없음."
        return
    }
    $new = ($entries | Where-Object { $_ -ne $projectRoot }) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $new, "User")
    Write-Host "Removed: '$projectRoot' 를 사용자 PATH에서 제거했습니다."
    Write-Host "새 터미널을 열면 적용됩니다."
    return
}

if ($entries -contains $projectRoot) {
    Write-Host "이미 PATH에 등록되어 있습니다: $projectRoot"
    Write-Host "변경할 게 없습니다."
    return
}

$new = ($entries + $projectRoot) -join ";"
[Environment]::SetEnvironmentVariable("Path", $new, "User")
Write-Host "Added to user PATH: $projectRoot"
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1) 현재 열려 있는 터미널/VSCode 창을 모두 닫았다가 다시 엽니다."
Write-Host "  2) 아무 폴더에서나 다음 명령을 사용할 수 있습니다:"
Write-Host "       ai_start"
Write-Host "       ai_finish"
Write-Host "       ai_commit"
Write-Host "       ai_record --help"
Write-Host ""
Write-Host "되돌리려면: .\scripts\install_ai_path.ps1 -Remove"
