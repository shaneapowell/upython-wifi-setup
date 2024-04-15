
/*****************
 * Simply show/hide the "loader" div element
 *****************/
function showLoader(show) {
  if (show == true) {
    document.getElementById("loader").removeAttribute("hidden");
  } else {
    document.getElementById("loader").hidden = true;
  }
}

