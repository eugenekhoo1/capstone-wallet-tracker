// Set up Infura API
const Web3 = require('web3');
const web3 = new Web3(// API provider);

// IMPT: Run EthereumETL before this step

// Extract list of transaction hashes
let path = './ethereumetl_files/transactions.csv';

const Papa = require('papaparse');
const fs = require('fs');
const file = fs.createReadStream(path)
const csv = require('csvtojson');
const fastcsv = require('fast-csv');

const { Client } = require('pg');
const { INSPECT_MAX_BYTES } = require('buffer');

const client = new Client({
    host: 'localhost',
    user: 'eugenekhoo',
    port: 5432,
    password: 'eugenekhoo',
    database: 'capstone'
})

// Read CSV file
async function getCSVData() { 
    const response = await csv().fromFile(path); 
    return response; 
} 

// API Call
async function transactionCall(item) {
    const promise = await web3.eth.getTransactionReceipt(item).then(function(results) {
        return constructObj(results)
    });
    return promise;
}

function constructObj(item) {
    var response = {
        "status" : item.status,
        "block_hash" : item.blockHash,
        "block_number" : item.blockNumber,
        "transaction_hash" : item.transactionHash,
        "transaction_index" : item.transctionIndex,
        "from_" : item.from,
        "to_" : item.to,
        "contract_address" : item.contractAddress,
        "cumulative_gas_used" : item.cumulativeGasUsed,
        "gas_used" : item.gasUsed,
        "logs" : JSON.stringify(item.logs),
        "effective_gas_price" : item.effectiveGasPrice
    }
    return response;
}

// Returns array of transaction receipts
async function iterate(data) {
    const toWrite = [];
    for (let i = 0; i < data.length; i++) {
        toWrite.push(transactionCall(data[i].hash));
    }
    const final = Promise.all(toWrite);
    return final;
}

function exportCSV(data) {
    const file = fs.createWriteStream('transaction_receipt.csv')
    fastcsv.write(data, {headers: true}).pipe(file).on('finish', () => {
        console.log('CSV exported');
    })
}

async function iterateAndExportCSV(data) {
    const final = iterate(data).then((value) => exportCSV(value)
    );
}

const csvData = getCSVData();
csvData.then((data) => iterateAndExportCSV(data));