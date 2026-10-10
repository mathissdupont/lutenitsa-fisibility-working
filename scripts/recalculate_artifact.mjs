/** Recalculate formula cells and verify finance against Python without modifying source inputs. */
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const expected=JSON.parse(await fs.readFile('output/qa/finance_expected.json','utf8'));
const results=[];
const close=(a,b)=>typeof a==='number' && Math.abs(a-b)<=Math.max(.01,Math.abs(b)*1e-8);
for(const [name,values] of Object.entries(expected)) {
  const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load(`output/qa/finance_${name}.xlsx`));
  workbook.recalculate();
  const summary=workbook.worksheets.getItem('PROFITABILITY_NPV').getRange('C6:I6').values[0];
  const checks={npv:close(summary[1],values.summary.npv),ebitda:close(summary[3],values.summary.ebitda),break_even_price:close(summary[4],values.summary.break_even_selling_price)};
  const schedule=workbook.worksheets.getItem('OPERATING_COSTS').getRange('D8:M31').values;
  checks.cashflows=values.rows.every((row,i)=>close(schedule[22][i],row.fcf));
  checks.tax=values.rows.every((row,i)=>close(schedule[16][i],row.taxes));
  checks.depreciation=values.rows.every((row,i)=>close(schedule[12][i],row.depreciation));
  if(!Object.values(checks).every(Boolean)) throw new Error(JSON.stringify({name,checks,summary,expected:values.summary,schedule}));
  results.push({name,checks});
}
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load('output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx'));
workbook.recalculate();
const cached=[];
for(let i=0;i<24;i++) {
  const sheet=workbook.worksheets.getItemAt(i);
  const used=sheet.getUsedRange();
  cached.push({sheet:sheet.name,values:used.values,formulas:used.formulas});
}
await fs.writeFile('output/qa/recalculated_cells.json',JSON.stringify(cached));
await fs.writeFile('reports/formula_verification.json',JSON.stringify({status:'PASS',engine:'artifact-tool',financial_checks:results,native_excel_status:'COM Workbooks.Open unavailable in execution session; independent formula engine used'},null,2));
console.log('Formula recalculation and three independent financial scenario checks passed.');
