param([string]$WorkbookPath = 'output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx')
# Recalculate only the newly generated workbook in a hidden Excel instance.
$resolvedWorkbook = (Resolve-Path -LiteralPath $WorkbookPath).Path
$recalculationCopy = Join-Path ([System.IO.Path]::GetTempPath()) ('fe401_recalc_' + [guid]::NewGuid().ToString('N') + '.xlsx')
Copy-Item -LiteralPath $resolvedWorkbook -Destination $recalculationCopy
$excelInstance = $null
$workbookObject = $null
try {
    $excelInstance = New-Object -ComObject Excel.Application
    $excelInstance.Visible = $false
    $excelInstance.DisplayAlerts = $false
    $excelInstance.AskToUpdateLinks = $false
    $workbookObject = $excelInstance.Workbooks.Open($recalculationCopy, 0, $false)
    $excelInstance.CalculateFullRebuild()
    $workbookObject.Save()
    $formulaCount = 0
    $errorCells = @()
    foreach ($sheetObject in $workbookObject.Worksheets) {
        try {
            $formulaCells = $sheetObject.UsedRange.SpecialCells(-4123)
            $formulaCount += $formulaCells.Count
        } catch { }
        try {
            $errors = $sheetObject.UsedRange.SpecialCells(-4123, 16)
            foreach ($cellObject in $errors.Cells) {
                $errorCells += "$($sheetObject.Name)!$($cellObject.Address()): $($cellObject.Text)"
            }
        } catch { }
    }
    @{ status = $(if ($errorCells.Count -eq 0) { 'success' } else { 'errors_found' }); total_formulas = $formulaCount; total_errors = $errorCells.Count; errors = $errorCells } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'reports/excel_recalculation.json' -Encoding UTF8
    Write-Output "Formulas: $formulaCount; errors: $($errorCells.Count)"
    if ($errorCells.Count -gt 0) { throw 'Workbook contains formula errors.' }
    $workbookObject.Close($false)
    Copy-Item -LiteralPath $recalculationCopy -Destination $resolvedWorkbook -Force
} finally {
    if ($workbookObject) { try { $workbookObject.Close($false) } catch { }; [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($workbookObject) }
    if ($excelInstance) { $excelInstance.Quit(); [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($excelInstance) }
    if (Test-Path -LiteralPath $recalculationCopy) { Remove-Item -LiteralPath $recalculationCopy }
}
