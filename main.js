const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

let flaskProcess;
let mainWindow;

function startFlaskServer() {
    console.log('Starting Flask server...');
    const pythonPath = path.join(__dirname, '.venv', 'Scripts', 'python.exe');  // Adjust the path if necessary
    flaskProcess = spawn(pythonPath, ['run_waitress.py'], {
        cwd: path.join(__dirname),
        env: { ...process.env, FLASK_ENV: 'production' }  // Set FLASK_ENV to production
    });

    flaskProcess.stdout.on('data', (data) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data) => {
        console.error(`Flask error: ${data}`);
    });

    flaskProcess.on('close', (code) => {
        console.log(`Flask process exited with code ${code}`);
    });

    return flaskProcess;
}

function createWindow() {
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
        mainWindow = null;
    });

    mainWindow.on('unresponsive', () => {
        console.error('The window is not responding');
    });

    mainWindow.on('crashed', () => {
        console.error('The window has crashed');
    });
}

function waitForServer(callback) {
    const interval = setInterval(() => {
        console.log('Checking if server is up...');
        http.get('http://127.0.0.1:5000', (res) => {
            console.log(`Received response with status code: ${res.statusCode}`);
            if (res.statusCode === 200 || res.statusCode === 302) {
                console.log('Server is up!');
                clearInterval(interval);
                callback();
            }
        }).on('error', (err) => {
            console.error('Error checking server status:', err);
        });
    }, 1000);  // Check every second
}

app.on('ready', () => {
    flaskProcess = startFlaskServer();
    setTimeout(() => waitForServer(createWindow), 5000);  // Wait 5 seconds before checking if the server is up
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', function () {
    if (mainWindow === null) {
        createWindow();
    }
});

app.on('will-quit', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }
});