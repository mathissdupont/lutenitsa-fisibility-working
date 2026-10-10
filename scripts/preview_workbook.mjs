/** Render bounded workbook regions using the supported artifact-tool API. */
import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile} from '@oai/artifact-tool';
const workbook=await SpreadsheetFile.importXlsx(await FileBlob.load('output/Lutenitsa_Factory_Feasibility_2015_2025.xlsx'));
await fs.mkdir('output/qa',{recursive:true});
for (const [sheetName,range] of [['DASHBOARD','B2:J22'],['RECIPE_MATERIAL_BALANCE','B2:L21'],['PROFITABILITY_NPV','B2:J8']]) {
  const preview=await workbook.render({sheetName,range,scale:1.5,format:'png'});
  await fs.writeFile(`output/qa/${sheetName}.png`,new Uint8Array(await preview.arrayBuffer()));
}
const inspected=await workbook.inspect({kind:'region',sheetId:'DASHBOARD',range:'B11:J17',maxChars:2000,tableMaxRows:7,tableMaxCols:9});
await fs.writeFile('reports/workbook_preview_inspection.json',JSON.stringify(inspected,null,2));
console.log('Rendered dashboard, material balance and financial summary.');
