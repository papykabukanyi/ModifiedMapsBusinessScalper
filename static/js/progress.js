var socket = io();

socket.on('connect', function() {
    console.log('Connected to server');
});

socket.on('progress', function(data) {
    var progress = data.progress;
    document.getElementById('progress-bar').style.width = progress + '%';
    document.getElementById('progress-text').innerText = progress + '% Complete';
});

socket.on('new_business', function(business) {
    var businessList = document.getElementById('business-list');
    var listItem = document.createElement('li');
    listItem.textContent = business.name + ' - ' + business.address + ' - ' + business.website + ' - ' + business.phone_number;
    businessList.appendChild(listItem);
});

socket.on('scrape_complete', function(data) {
    document.getElementById('excel-link').href = data.excel_url;
    alert('Scraping complete! You can download the file now.');
});
