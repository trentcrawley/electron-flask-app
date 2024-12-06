const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');
const fs = require('fs');

let flaskProcess;
let mainWindow;

function logToFile(message) {
    const logMessage = `${new Date().toISOString()} - ${message}\n`;
    fs.appendFileSync('electron.log', logMessage);
    console.log(logMessage);
}

// Log the value of NODE_ENV
logToFile(`NODE_ENV is set to: ${process.env.NODE_ENV}`);

function startFlaskServer() {
    logToFile('Starting Flask server...');
    let pythonPath;
    let scriptPath;
    let workingDirectory;
    if (process.env.NODE_ENV === 'development') {
        pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe');  // Adjust the path if necessary
        scriptPath = path.join(__dirname, 'run_waitress.py');  // Adjust the path if necessary
        workingDirectory = __dirname;
    } else {
        pythonPath = path.join(process.resourcesPath, '.venv', 'Scripts', 'python.exe');  // Adjust the path if necessary
        scriptPath = path.join(process.resourcesPath, 'run_waitress.py');  // Adjust the path if necessary
        workingDirectory = process.resourcesPath;
    }

    logToFile(`Using Python executable at: ${pythonPath}`);
    logToFile(`Using script at: ${scriptPath}`);
    logToFile(`Current working directory: ${workingDirectory}`);

    flaskProcess = spawn(pythonPath, [scriptPath], {
        cwd: workingDirectory,  // Ensure this is the correct working directory
        env: { ...process.env, FLASK_ENV: 'production' }  // Set FLASK_ENV to production
    });

    flaskProcess.stdout.on('data', (data) => {
        logToFile(`Flask stdout: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        logToFile(`Flask stderr: ${data}`);
    });

    flaskProcess.on('error', (err) => {
        logToFile(`Failed to start Flask server: ${err}`);
    });

    flaskProcess.on('close', (code) => {
        logToFile(`Flask process exited with code ${code}`);
    });

    return flaskProcess;
}

function createWindow() {
    logToFile('Creating main window...');
    mainWindow = new BrowserWindow({
        width: 1000,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    mainWindow.loadURL('http://127.0.0.1:5000/');  // Load the Flask app URL

    mainWindow.on('closed', function () {
        logToFile('Main window closed');
        mainWindow = null;
    });

    mainWindow.on('unresponsive', () => {
        logToFile('The window is not responding');
    });

    mainWindow.on('crashed', () => {
        logToFile('The window has crashed');
    });
}

function waitForServer(callback) {
    const interval = setInterval(() => {
        logToFile('Checking if server is up...');
        http.get('http://127.0.0.1:5000', (res) => {
            logToFile(`Received response with status code: ${res.statusCode}`);
            if (res.statusCode === 200 || res.statusCode === 302) {
                logToFile('Server is up!');
                clearInterval(interval);
                callback();
            }
        }).on('error', (err) => {
            logToFile(`Error checking server status: ${err}`);
        });
    }, 1000);  // Check every second
}

app.on('ready', () => {
    flaskProcess = startFlaskServer();
    setTimeout(() => waitForServer(createWindow), 5000);  // Wait 5 seconds before checking if the server is up
});

app.on('window-all-closed', function () {
    logToFile('All windows closed');
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    logToFile('App activated');
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    logToFile('App will quit');
    if (flaskProcess) {
        flaskProcess.kill();
    }
});