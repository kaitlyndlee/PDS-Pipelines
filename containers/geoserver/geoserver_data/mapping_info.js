// features will contain all objects
// just iterate through it like an array
// make sure to use JSON.parse() to get an object you can select from
// how will it handle the coordinates category?
  // is this something I would need to worry about iterating through or could I just give the file the array?

var xhttp = new XMLHttpRequest();

var url = "http://localhost:8080/geoserver/PDS/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=PDS%3Aeuropa_view&maxFeatures=50&outputFormat=application%2Fjson";
xhttp.open("GET", url, false);
xhttp.send();
console.log("finished");


// use fetch to get the url
// this could work better?????
/*
const url = "http://localhost:8080/geoserver/PDS/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=PDS%3Aeuropa_view&maxFeatures=50&outputFormat=application%2Fjson";

fetch(url)
  .then((response) => {
    if (response.ok) {
		console.log(response)
      return response.json()
    }
  })
  .then((json) => {
    birds.push(...json['birds'])
	console.log(birds)
  })
  */


/*
	var table = document.getElementById("planet_table");

	// get the url and load the data into a variable
	// loop through

	// need to add items to elements

	const elements = [];

	let row_index = 0;

	for (item in elements)
	{
		let object = JSON.parse(item);

		if (object)
		{
			var new_row = table.insertRow(index_goes_here);
			row_index++;

			// do I need to insert a cell? Can I just change the info?
			//var value_1 = new_row.insertCell(0);

			var columns = table.rows[row_index].cells;
			columns[0].innerHTML = object.planet;
		}
	}

  for (json_item in json_keys)
  {
    // need to add the json data to another table
    // this should be inside the other loop
  }


	// can I take the amount of columns that already exist in the table and then
	// use that to find the number of rows?
	// since the object info is specific this might not work
	// object.value

*/
