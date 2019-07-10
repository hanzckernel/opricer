var myVar;

function myFunction() {
  myVar = setTimeout(showPage, 3000);
}

function showPage() {
  document.getElementById("_dash-loading").style.display = "none";
  document.getElementById("content-main").style.display = "block";
}
