# DatasetReader.psm1 - Module for reading BC-Bench dataset
# Provides classes and functions to read and parse the bcbench.jsonl dataset

class TestEntry {
    [int]$codeunitID
    [string[]]$functionName

    TestEntry([PSObject]$jsonObject) {
        $this.codeunitID = [int]$jsonObject.codeunitID
        $this.functionName = $jsonObject.functionName
    }
}

class ValidationResult {
    [string]$InstanceId
    [string]$Status
    [string]$Message

    ValidationResult([string]$instanceId, [string]$status, [string]$message) {
        $this.InstanceId = $instanceId
        $this.Status = $status
        $this.Message = $message
    }
}

class DatasetEntry {
    # Properties based on the dataset schema
    [string]$repo
    [string]$instance_id
    [string]$patch
    [string]$base_commit
    [string]$hints_text
    [string]$created_at
    [string]$test_patch
    [string]$problem_statement
    [string]$environment_setup_version
    [TestEntry[]]$FAIL_TO_PASS
    [TestEntry[]]$PASS_TO_PASS
    [string[]]$project_paths

    # Constructor that takes a PSObject (from JSON)
    DatasetEntry([PSObject]$jsonObject) {
        $this.repo = $jsonObject.repo
        $this.instance_id = $jsonObject.instance_id
        $this.patch = $jsonObject.patch
        $this.base_commit = $jsonObject.base_commit
        $this.hints_text = $jsonObject.hints_text
        $this.created_at = $jsonObject.created_at
        $this.test_patch = $jsonObject.test_patch
        $this.problem_statement = $jsonObject.problem_statement
        $this.environment_setup_version = $jsonObject.environment_setup_version
        $this.FAIL_TO_PASS = @()
        foreach ($entry in $jsonObject.FAIL_TO_PASS) {
            $this.FAIL_TO_PASS += [TestEntry]::new($entry)
        }
        $this.PASS_TO_PASS = @()
        foreach ($entry in $jsonObject.PASS_TO_PASS) {
            $this.PASS_TO_PASS += [TestEntry]::new($entry)
        }
        $this.project_paths = $jsonObject.project_paths
    }

    # Helper method to get a summary string
    [string]ToString() {
        return "DatasetEntry: $($this.instance_id) (Repo: $($this.repo), Version: $($this.environment_setup_version))"
    }
}

function Get-DatasetEntries {
    [CmdletBinding()]
    [OutputType([DatasetEntry[]])]

    param(
        [Parameter(Mandatory = $true)]
        [string]$DatasetPath,

        [Parameter(Mandatory = $false)]
        [string]$Version,

        [Parameter(Mandatory = $false)]
        [string]$InstanceId
    )

    if (-not (Test-Path $DatasetPath)) {
        throw "Dataset file not found at: $DatasetPath"
    }

    if ($Version -and $InstanceId) {
        throw "Please provide either Version or InstanceId, not both."
    }

    Write-Verbose "Reading dataset from: $DatasetPath"
    [DatasetEntry[]] $entries = @()

    $content = Get-Content $DatasetPath -Raw
    $jsonObjects = $content -split '(?<=})\s*\n(?=\{)' | Where-Object { $_.Trim().Length -gt 0 }

    foreach ($jsonString in $jsonObjects) {
        try {
            $jsonObject = $jsonString.Trim() | ConvertFrom-Json
            $DatasetEntry = [DatasetEntry]::new($jsonObject)
            $entries += $DatasetEntry
            Write-Verbose "Loaded entry: $($DatasetEntry.instance_id)"
        }
        catch {
            Write-Warning "Failed to parse JSON object: $_"
        }
    }

    if ($Version) {
        $entries = $entries | Where-Object { $_.environment_setup_version -eq $Version }
    }
    elseif ($InstanceId) {
        $entries = $entries | Where-Object { $_.instance_id -eq $InstanceId }
    }

    Write-Verbose "Successfully loaded $($entries.Count) dataset entries"
    return $entries
}

function Get-CounterfactualDatasetEntry {
    [CmdletBinding()]
    [OutputType([DatasetEntry])]

    param(
        [Parameter(Mandatory = $true)]
        [string]$InstanceId,

        [Parameter(Mandatory = $false)]
        [string]$CounterfactualDatasetPath = (Get-BCBenchDatasetPath -DatasetName "counterfactual.jsonl"),

        [Parameter(Mandatory = $false)]
        [string]$BaseDatasetPath = (Get-BCBenchDatasetPath)
    )

    if (-not (Test-Path $CounterfactualDatasetPath)) {
        throw "Counterfactual dataset not found at: $CounterfactualDatasetPath"
    }

    # Find the CF entry in counterfactual.jsonl
    $cfContent = Get-Content $CounterfactualDatasetPath -Raw
    $cfJsonObjects = $cfContent -split '(?<=})\s*\n(?=\{)' | Where-Object { $_.Trim().Length -gt 0 }

    $cfJson = $null
    foreach ($jsonString in $cfJsonObjects) {
        $parsed = $jsonString.Trim() | ConvertFrom-Json
        if ($parsed.instance_id -eq $InstanceId) {
            $cfJson = $parsed
            break
        }
    }

    if (-not $cfJson) {
        throw "Counterfactual entry '$InstanceId' not found in $CounterfactualDatasetPath"
    }

    # Load the base entry
    [string] $baseInstanceId = $cfJson.base_instance_id
    [DatasetEntry[]] $baseEntries = Get-DatasetEntries -DatasetPath $BaseDatasetPath -InstanceId $baseInstanceId
    if ($baseEntries.Count -eq 0) {
        throw "Base entry '$baseInstanceId' not found in $BaseDatasetPath"
    }

    [DatasetEntry] $base = $baseEntries[0]

    # Merge: take infrastructure from base, test/patch data from CF
    $merged = @{
        repo                      = $base.repo
        instance_id               = $cfJson.instance_id
        base_commit               = $base.base_commit
        environment_setup_version = $base.environment_setup_version
        project_paths             = $base.project_paths
        patch                     = $cfJson.patch
        test_patch                = $cfJson.test_patch
        FAIL_TO_PASS              = $cfJson.FAIL_TO_PASS
        PASS_TO_PASS              = if ($cfJson.PASS_TO_PASS) { $cfJson.PASS_TO_PASS } else { @() }
        hints_text                = $base.hints_text
        created_at                = $base.created_at
        problem_statement         = $base.problem_statement
    }

    return [DatasetEntry]::new([PSCustomObject]$merged)
}

Export-ModuleMember -Function Get-DatasetEntries, Get-CounterfactualDatasetEntry
