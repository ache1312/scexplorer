const express = require("express");
const bodyParser = require("body-parser");
const multer = require("multer");
const path = require("path");

const app = express();
const PORT = 3000;

// Configure storage for file uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, path.join(__dirname, "upload")) // Make sure this path matches the Docker volume
  },
  filename: function (req, file, cb) {
    cb(null, file.fieldname + "-" + Date.now() + path.extname(file.originalname));
  }
});
const upload = multer({ storage: storage });

// App setup
app.set("view engine", "ejs");
app.set("views", path.join(__dirname, "views"));
app.use(express.static(path.join(__dirname, "public")));
// Serve under /scexplorer for compatibility with hosted path
app.use("/scexplorer", express.static(path.join(__dirname, "public")));
app.use("/upload", express.static(path.join(__dirname, "upload")));
app.use(bodyParser.urlencoded({ extended: true }));

// Dynamic frontend config for backend base URL
app.get('/config.js', (_req, res) => {
  const backend = process.env.BACKEND_URL || 'http://localhost:8000/backend';
  res.type('application/javascript').send(`window.API_BASE_URL = '${backend}';`);
});
// Also expose at /scexplorer/config.js
app.get('/scexplorer/config.js', (_req, res) => {
  const backend = process.env.BACKEND_URL || 'http://localhost:8000/backend';
  res.type('application/javascript').send(`window.API_BASE_URL = '${backend}';`);
});

// Routes
app.get("/", (req, res) => {
  res.render("home");
});
app.get("/scexplorer", (req, res) => {
  res.render("home");
});

app.get("/upload", (req, res) => {
  res.render("upload");
});
app.get("/scexplorer/upload", (req, res) => {
  res.render("upload");
});

app.get("/preprocess", (req, res) => {
  res.render("preprocess");
});
app.get("/scexplorer/preprocess", (req, res) => {
  res.render("preprocess");
});

app.get("/embedding", (req, res) => {
  res.render("embedding");
});
app.get("/scexplorer/embedding", (req, res) => {
  res.render("embedding");
});

app.get("/labeling", (req, res) => {
  res.render("labeling");
});
app.get("/scexplorer/labeling", (req, res) => {
  res.render("labeling");
});

app.get("/dea", (req, res) => {
  res.render("dea");
});
app.get("/scexplorer/dea", (req, res) => {
  res.render("dea");
});

app.get("/integration", (req, res) => {
  res.render("integration");
});
app.get("/scexplorer/integration", (req, res) => {
  res.render("integration");
});

app.get('/results', (req, res) => {
  res.render('results');
});
app.get('/scexplorer/results', (req, res) => {
  res.render('results');
});

app.get('/visualization', (req, res) => {
  res.render('visualization');
});
app.get('/scexplorer/visualization', (req, res) => {
  res.render('visualization');
});

app.get('/heatmap', (req, res) => {
  res.render('heatmap');
});
app.get('/scexplorer/heatmap', (req, res) => {
  res.render('heatmap');
});

app.post("/submit", upload.array("dataFiles"), (req, res) => {
  res.send("Form submitted!");
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
