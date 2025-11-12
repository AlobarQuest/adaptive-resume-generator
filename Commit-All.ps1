#Requires -Version 5.1
[CmdletBinding()]
param(
  [switch]$NoTest,
  [switch]$NoPush
)

# Always run from the folder containing this script
if ($PSScriptRoot) { Set-Location -LiteralPath $PSScriptRoot }
Write-Host "Running in: $((Get-Location).Path)" -ForegroundColor DarkGray

# Resolve full path to git.exe
$global:GitExe = (Get-Command git -ErrorAction Stop).Source

function Exec($cmd, $errMsg) {
  $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $cmd" -NoNewWindow -PassThru -Wait
  if ($p.ExitCode -ne 0) { throw $errMsg }
}

function GitOut([string]$argLine) {
  $parts = $argLine -split ' '
  $out = & $GitExe -C $((Get-Location).Path) @parts 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git $argLine failed: $out" }
  return ($out -join "`n").TrimEnd()
}

function Confirm-GitRepo {
  try { GitOut "rev-parse --is-inside-work-tree" | Out-Null } catch { throw "Not a git repository." }
}

function Get-Branch { GitOut "rev-parse --abbrev-ref HEAD" }

function Get-StatusPorcelain {
  $out = GitOut "status --porcelain"
  if ([string]::IsNullOrWhiteSpace($out)) { return @() }
  # FIX: use regex newline split, not backtick escapes
  return $out -split "\r?\n" | Where-Object { $_ -ne "" }
}

function Show-Status {
  Write-Host "`n--- Git Status ---" -ForegroundColor Cyan
  Exec "git -c color.status=always status --short --branch" "git status failed"
  Write-Host "-------------------`n" -ForegroundColor Cyan
}

function Select-FilesToStage {
  $lines = Get-StatusPorcelain
  if (-not $lines -or $lines.Count -eq 0) { return @{ Paths = @(); IsAll = $false } }

  $entries = @()
  $i = 1
  foreach ($l in $lines) {
    # Porcelain: 2 status chars, spaces, then path (renames: "old -> new")
    $m = [regex]::Match($l, '^(..)\s+(.*)$')
    if (-not $m.Success) { continue }
    $status = $m.Groups[1].Value.Trim()
    $rawPath = $m.Groups[2].Value.Trim()
    if ($rawPath -like '* -> *') {
      $parts = $rawPath -split '\s+->\s+', 2
      if ($parts.Count -eq 2) { $rawPath = $parts[1] }
    }
    $entries += [pscustomobject]@{ Index = $i; Status = $status; Path = $rawPath }
    $i++
  }

  Write-Host "Unstaged/Untracked files:" -ForegroundColor Yellow
  foreach ($e in $entries) {
    Write-Host ("[{0}] {1,-2} {2}" -f $e.Index, $e.Status, $e.Path)
  }

  $choice = Read-Host "Stage (A)ll, (N)one, or select by comma (e.g. 1,3,5) [A]"
  $choice = if ([string]::IsNullOrWhiteSpace($choice)) { "a" } else { $choice.Trim().ToLower() }

  switch -Regex ($choice) {
    '^a' { return @{ Paths = $entries.Path; IsAll = $true } }
    '^n' { return @{ Paths = @(); IsAll = $false } }
    default {
      $nums = $choice -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -match '^\d+$' } | ForEach-Object {[int]$_}
      if ($nums.Count -eq 0) { return @{ Paths = @(); IsAll = $false } }
      $selected = @()
      foreach ($n in $nums) {
        $match = $entries | Where-Object { $_.Index -eq $n }
        if ($match) { $selected += $match.Path }
      }
      return @{ Paths = $selected; IsAll = $false }
    }
  }
}

function Stage-Files($paths) {
  if (-not $paths -or $paths.Count -eq 0) { return }
  foreach ($p in $paths) {
    Exec "git add -- `"$p`"" "Failed to stage $p"
  }
}

function Get-ProjectName {
  if (Test-Path "pyproject.toml") {
    $nameLine = (Select-String -Path "pyproject.toml" -Pattern '^\s*name\s*=\s*"(.*)"' -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($nameLine) {
      $m = [regex]::Match($nameLine.Line, 'name\s*=\s*"(.*)"')
      if ($m.Success) { return $m.Groups[1].Value }
    }
  }
  $pkg = Get-ChildItem -Directory | Where-Object { Test-Path (Join-Path $_.FullName "__init__.py") } | Select-Object -First 1
  if ($pkg) { return $pkg.Name }
  return ""
}

function Get-Version {
  if (Test-Path "pyproject.toml") {
    $verLine = (Select-String -Path "pyproject.toml" -Pattern '^\s*version\s*=\s*"(.*)"' -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($verLine) {
      $m = [regex]::Match($verLine.Line, 'version\s*=\s*"(.*)"')
      if ($m.Success) { return $m.Groups[1].Value }
    }
  }
  return ""
}

function Bump-Version([string]$level) {
  if (-not (Test-Path "pyproject.toml")) { Write-Host "No pyproject.toml; skip version bump." -ForegroundColor DarkYellow; return $null }
  $current = Get-Version
  if (-not $current) { Write-Host "Unable to read current version; skip bump." -ForegroundColor DarkYellow; return $null }
  $parts = $current.Split('.')
  while ($parts.Count -lt 3) { $parts += "0" }
  $major=[int]$parts[0]; $minor=[int]$parts[1]; $patch=[int]$parts[2]
  switch ($level.ToLower()) {
    "major" { $major++; $minor=0; $patch=0 }
    "minor" { $minor++; $patch=0 }
    default  { $patch++ }
  }
  $new = "$major.$minor.$patch"

  $content = Get-Content -LiteralPath "pyproject.toml" -Raw
  $content = $content -replace '(^\s*version\s*=\s*")[^"]+(")', ("`$1$($new)`$2")
  Set-Content -LiteralPath "pyproject.toml" -Value $content -Encoding UTF8

  Write-Host "Version bumped: $current -> $new" -ForegroundColor Green
  return $new
}

function Detect-Pytest {
  if (Test-Path ".\pytest.ini") { return $true }
  if ((Test-Path ".\pyproject.toml") -and (Select-String -Path "pyproject.toml" -Pattern '\[tool\.pytest\]' -Quiet)) { return $true }
  if ((Test-Path ".\tests") -and ((Get-ChildItem .\tests -Recurse -Include *.py | Measure-Object).Count -gt 0)) { return $true }
  return $false
}

function Run-Tests {
  if (-not (Detect-Pytest)) { return $true }
  $resp = if ($NoTest) {'n'} else { Read-Host "Run tests with 'pytest -q' before commit? (Y/n)" }
  if ($resp.Trim().ToLower() -eq 'n') { return $true }
  try {
    Exec "pytest -q" "Tests failed"
    Write-Host "Tests passed." -ForegroundColor Green
    return $true
  } catch {
    Write-Host "Tests failed." -ForegroundColor Red
    $cont = Read-Host "Proceed with commit anyway? (y/N)"
    return ($cont.Trim().ToLower() -eq 'y')
  }
}

function Pick-Type {
  $types = @("feat","fix","docs","style","refactor","perf","test","build","ci","chore","revert")
  Write-Host "Commit types: $($types -join ', ')" -ForegroundColor Cyan
  $t = Read-Host "Type"
  if (-not $types.Contains($t)) {
    Write-Host "Unknown type; defaulting to 'chore'." -ForegroundColor DarkYellow
    return "chore"
  }
  return $t
}

function Read-Multiline($prompt) {
  Write-Host "$prompt  (finish with a single '.' on its own line):"
  $lines = New-Object System.Collections.Generic.List[string]
  while ($true) {
    $line = Read-Host
    if ($line -eq ".") { break }
    $lines.Add($line)
  }
  return ($lines -join "`n")
}

# --- Main ---
try {
  Confirm-GitRepo
  Show-Status

  $porcelain = Get-StatusPorcelain
  if (-not $porcelain) {
    Write-Host "No changes detected. Nothing to commit." -ForegroundColor Yellow
    return
  }

  $sel = Select-FilesToStage
  if ($sel.IsAll) {
    Exec "git add -A -- :/" "Failed to stage all changes"
  } elseif ($sel.Paths -and $sel.Paths.Count -gt 0) {
    Stage-Files $sel.Paths
  } else {
    Write-Host "No files staged. (If you intended to stage all, rerun and choose A.)" -ForegroundColor Yellow
  }

  Write-Host "`n--- Staged files ---" -ForegroundColor Cyan
  Exec "git -c color.status=always diff --cached --name-status" "git diff --cached failed"
  $stagedCheck = GitOut "diff --cached --name-only"
  if (-not $stagedCheck) {
    Write-Host "Nothing staged; exiting." -ForegroundColor Yellow
    return
  }

  $branch = Get-Branch
  Write-Host "`nOn branch: $branch" -ForegroundColor DarkCyan

  $type = Pick-Type
  $project = Get-ProjectName
  $defaultScope = if ($project) { $project } else { "" }
  $scope = Read-Host "Scope (optional) [$defaultScope]"
  if ([string]::IsNullOrWhiteSpace($scope)) { $scope = $defaultScope }

  $subject = Read-Host "Short description (subject, <= 72 chars)"
  if ($subject.Length -gt 72) { Write-Host "Trimming subject to 72." -ForegroundColor DarkYellow; $subject = $subject.Substring(0,72) }

  $body = Read-Multiline "Commit body (optional)"
  $breaking = Read-Host "Breaking change? (y/N)"
  $breakingText = ""
  if ($breaking.Trim().ToLower() -eq 'y') {
    $breakingText = Read-Multiline "Describe the breaking change"
  }

  $issue = Read-Host "Issue/PR number to close (optional, just digits)"
  $footer = @()
  if ($breakingText) { $footer += "BREAKING CHANGE: $breakingText" }
  if ($issue -match '^\d+$') { $footer += "Closes #$issue" }

  $versionNew = $null
  if (Test-Path "pyproject.toml") {
    $curVer = Get-Version
    if ($curVer) {
      $bump = Read-Host "Bump version in pyproject.toml? (none/patch/minor/major) [none]"
      if ($bump -and $bump.ToLower() -ne "none") {
        $versionNew = Bump-Version $bump
        if ($versionNew) {
          Exec "git add -- pyproject.toml" "Failed to stage pyproject.toml"
        }
      }
    }
  }

  if (-not (Run-Tests)) { Write-Host "Aborting due to tests." -ForegroundColor Red; return }

  $scopePart = if ($scope) { "($scope)" } else { "" }
  $bang = if ($breakingText) { "!" } else { "" }
  $header = "$($type)$($scopePart)$($bang): $subject"

  $msgParts = @($header)
  if ($body) { $msgParts += ""; $msgParts += $body }
  if ($versionNew) { $msgParts += ""; $msgParts += "Release: $versionNew" }
  if ($footer.Count -gt 0) { $msgParts += ""; $msgParts += ($footer -join "`n") }
  $fullMsg = $msgParts -join "`n"

  $tmp = New-TemporaryFile
  Set-Content -Path $tmp -Value $fullMsg -Encoding UTF8

  Exec "git commit -F `"$tmp`"" "git commit failed"
  Remove-Item $tmp -Force

  if ($versionNew) {
    $tagName = "v$versionNew"
    try {
      Exec "git tag $tagName" "tag failed"
      Write-Host "Tagged $tagName" -ForegroundColor Green
    } catch { Write-Host "Skipping tag; already exists?" -ForegroundColor DarkYellow }
  }

  if (-not $NoPush) {
    $hasUpstream = $true
    try { GitOut "rev-parse --abbrev-ref --symbolic-full-name @{u}" | Out-Null } catch { $hasUpstream = $false }
    if (-not $hasUpstream) {
      $doUpstream = Read-Host "No upstream for '$branch'. Push and set upstream? (Y/n)"
      if ($doUpstream.Trim().ToLower() -ne 'n') {
        Exec "git push -u origin $branch" "git push failed"
        if ($versionNew) { Exec "git push --tags" "push tags failed" }
        Write-Host "Pushed with upstream." -ForegroundColor Green
        return
      }
    } else {
      $doPush = Read-Host "Push now? (Y/n)"
      if ($doPush.Trim().ToLower() -ne 'n') {
        Exec "git push" "git push failed"
        if ($versionNew) { Exec "git push --tags" "push tags failed" }
        Write-Host "Pushed." -ForegroundColor Green
      }
    }
  }

  Write-Host "`nDone." -ForegroundColor Green
}
catch {
  Write-Host $_.Exception.Message -ForegroundColor Red
  exit 1
}
