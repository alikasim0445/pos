// utils/exportUtils.ts

// Function to convert data to CSV format
export const convertToCSV = (data: any[]): string => {
  if (data.length === 0) return '';
  
  // Get headers from the first object's keys
  const headers = Object.keys(data[0]);
  
  // Create header row
  const headerRow = headers.join(',');
  
  // Create data rows
  const dataRows = data.map(row => {
    return headers.map(header => {
      const value = row[header];
      // Escape commas and quotes in values
      if (typeof value === 'string' && (value.includes(',') || value.includes('"') || value.includes('\n'))) {
        return `"${value.replace(/"/g, '""')}"`;
      }
      return value;
    }).join(',');
  });
  
  // Combine header and data rows
  return [headerRow, ...dataRows].join('\n');
};

// Function to download CSV file
export const downloadCSV = (data: any[], filename: string) => {
  const csvContent = convertToCSV(data);
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  // Create a download link
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  // Append to the document, click, and remove
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Function to convert data to Excel format (as CSV for simplicity)
export const downloadExcel = (data: any[], filename: string) => {
  // For now, using the same CSV format
  // In a real implementation, we would use a library like xlsx
  const csvContent = convertToCSV(data);
  const blob = new Blob([csvContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8;' });
  
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename.replace('.csv', '.xlsx'));
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Function to generate PDF (simplified - would need more complex implementation in real app)
export const downloadPDF = (data: any[], filename: string, reportTitle: string = 'Report') => {
  // Create HTML content for PDF
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>${reportTitle}</title>
      <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .header { text-align: center; margin-bottom: 20px; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>${reportTitle}</h1>
        <p>Generated on: ${new Date().toLocaleString()}</p>
      </div>
      <table>
        <thead>
          <tr>
            ${data.length > 0 ? Object.keys(data[0]).map(key => `<th>${key}</th>`).join('') : ''}
          </tr>
        </thead>
        <tbody>
          ${data.map(row => {
            return '<tr>' + Object.values(row).map(value => `<td>${value}</td>`).join('') + '</tr>';
          }).join('')}
        </tbody>
      </table>
    </body>
    </html>
  `;
  
  const blob = new Blob([htmlContent], { type: 'application/pdf' });
  
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename.replace('.csv', '.pdf'));
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Function to export table data
export const exportTableData = (
  data: any[],
  format: 'csv' | 'excel' | 'pdf',
  filename: string,
  reportTitle: string = 'Report'
) => {
  switch (format) {
    case 'csv':
      downloadCSV(data, filename);
      break;
    case 'excel':
      downloadExcel(data, filename);
      break;
    case 'pdf':
      downloadPDF(data, filename, reportTitle);
      break;
    default:
      downloadCSV(data, filename);
  }
};