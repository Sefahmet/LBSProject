/**** old line array to clear layers ***/
const oldLineArr = [];

/**** UTIL METHODS ******/
const getRandomHexColorStyle = () => {

    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    const createdStyle = new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: color,
            width: 4,
            opacity: 1
        })
    });
    return createdStyle;
};

const addLayer = (layer, addToOldLineArr = true) => {
    MAP.addLayer(layer);
    if (addToOldLineArr) {
        oldLineArr.push(layer);
    }
};

const clearLayer = (layer) => {
    MAP.removeLayer(layer);
};

const createLayerVector = (features) => {
    return new ol.layer.Vector({
        source: new ol.source.Vector({
            features: features
        })
    });
};

const clearOldLayers = () => {
    if (oldLineArr.length > 0) {
        oldLineArr.forEach(item => clearLayer(item));
        oldLineArr.splice(0, oldLineArr.length);
    }
};
/************* --------------------- *************/

/**** CONSTANTS ******/
const GROUP_NAME = "lbs2024";
const BASE_URL = "http://127.0.0.1:8000";; // when running locally
// const BASE_URL = "https://geonet.igg.uni-bonn.de"; // when uploading to server
const LEFT_BOTTOM = ol.proj.transform([7.004813999686911, 50.67771640948173], "EPSG:4326", "EPSG:3857");
const RIGHT_TOP = ol.proj.transform([7.19776199427912, 50.768218129933224], "EPSG:4326", "EPSG:3857");
/**** -------- *****/


/**** MIN_MAX_COORDS *****/
const MIN_X = LEFT_BOTTOM[0];
const MIN_Y = LEFT_BOTTOM[1];
const MAX_X = RIGHT_TOP[0];
const MAX_Y = RIGHT_TOP[1];
/**** -------- *****/


/****** MARKER ICONS ******/
const FIRST_MARKER_ICON = new ol.style.Style({
    // The marker fetching from open source web service. If it is not working, please change the image link
    // you can add any png image from web ( Don't Forget to set the scale )
    image: new ol.style.Icon({
        crossOrigin: 'anonymous',
        src: 'https://cdn1.iconfinder.com/data/icons/web-55/32/web_1-1024.png',
        scale: "0.03"
    }),
});

const SECOND_MARKER_ICON = new ol.style.Style({
    // The marker fetching from open source web service.  If it is not working, please change the image link
    // you can add any png image from web ( Don't Forget to set the scale )
    image: new ol.style.Icon({
        crossOrigin: 'anonymous',
        src: 'https://cdn4.iconfinder.com/data/icons/twitter-29/512/157_Twitter_Location_Map-1024.png',
        scale: "0.04"
    }),
});
/**** -------- *****/

/****** MARKERS ******/
const FIRST_MARKER = new ol.Feature({
    geometry: new ol.geom.Point(1,1)
});
FIRST_MARKER.setStyle(FIRST_MARKER_ICON);

const SECOND_MARKER = new ol.Feature({
    geometry: new ol.geom.Point(1,1)
});
SECOND_MARKER.setStyle(SECOND_MARKER_ICON);
/**** -------- *****/


/***** INPUT ELEMENTS *****/
const firstCoordInput = document.getElementById("coord1");
const secondCoordInput = document.getElementById("coord2");
/**** -------- *****/


/****** LAYERS ******/
const TILE_LAYER = new ol.layer.Tile({ source: new ol.source.OSM()});
/**** -------- *****/


/**** MAP ****/
const MAP = new ol.Map({
    target: 'map',
    layers: [
        TILE_LAYER
    ],
    view: new ol.View({
        center: ol.proj.fromLonLat([(MIN_X + MAX_X)/2, (MAX_Y + MIN_Y)/2]),
        zoom: 2,
        maxZoom: 20,
        minZoom: 2,
        extent: [MIN_X, MIN_Y, MAX_X, MAX_Y],
    })
});
/**** -------- *****/

/***** PRESET STYLE *****/
const WALK_LINE_STYLE = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#0080ff',
        width: 4,
        opacity: 1,
        lineDash: [.1, 7]
    })
});
const TRAM_LINE_STYLE  = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#00ffea',
        width: 4,
        opacity: 1
    })
})
const BUS_LINE_STYLE = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#010501',
        width: 4,
        opacity: 1
    })
})

const TRAIN_LINE_STYLE = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#ff8900',
        width: 4,
        opacity: 1
    })
})
const TRANSFER_LINE_STYLE = new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#272626',
        width: 4,
        opacity: 1,
        lineDash: [.1, 7]
    })
})
/**** -------- *****/

/***** VARIABLES *****/
let counter = 0;
let firstMarkerLayer;
let secondMarkerLayer;
let routeMethod = "shortestpath";
let pathMethod = "singlepath";
let ptCount = 0;
/**** -------- *****/



function drawPath(path) {
    console.log(path);
    clearOldLayers();
    const points = [];

    // for (let i = 0; i < path.length; i++) {
    //     let coord = path[i];
    //     let point = ol.proj.fromLonLat([coord.x, coord.y]);
    //     console.log(coord)
    //     console.log(point);
    //     points.push(point);
    // }

    let lineString = new ol.geom.LineString(path);
    let lineFeature = new ol.Feature({
        geometry: lineString
    });

    lineFeature.setStyle(WALK_LINE_STYLE);
    line = createLayerVector([lineFeature]);
    addLayer(line);
}


function drawMultiModalPath(path) {
    clearOldLayers();
    const path_list = path.paths;
    const path_ids = path.tags;
    const path_times = path.times;

    for (let i = 0; i < path_ids.length; i++) {
        let lineString = new ol.geom.LineString(path_list[i]);
        let lineFeature = new ol.Feature({ geometry: lineString });

        let type = path_ids[i][0];
        let name = path_ids[i][1];
        let timeInfo = path_times[i];
        let timeText = (timeInfo && timeInfo[0] && timeInfo[1]) ? `${timeInfo[0]} - ${timeInfo[1]}` : timeInfo ? timeInfo[0] : "";

        let lineStyle;
        if (type === "bus") {
            lineStyle = new ol.style.Style({ stroke: new ol.style.Stroke({ color: '#010501', width: 4 }) });
        } else if (type === "tram") {
            lineStyle = new ol.style.Style({ stroke: new ol.style.Stroke({ color: '#00ffea', width: 4 }) });
        } else if (type === "train") {
            lineStyle = new ol.style.Style({ stroke: new ol.style.Stroke({ color: '#ff8900', width: 4 }) });
        } else if (type === "walk") {
            lineStyle = new ol.style.Style({ stroke: new ol.style.Stroke({ color: '#0080ff', width: 4, lineDash: [.1, 7] }) });
        } else if (type === "transfer") {
            lineStyle = new ol.style.Style({ stroke: new ol.style.Stroke({ color: '#272626', width: 4, lineDash: [.1, 7] }) });
        }

        lineFeature.setStyle(lineStyle);
        const line = createLayerVector([lineFeature]);
        addLayer(line);
    }

    // **Legend'ı Güncelle**
    updateLegend(path);
}

/**** EVENT LISTENERS ****/
document.getElementById('toggleBtn').addEventListener('change', function(e) {
    routeMethod = e.target.checked ?  "multimodalroute" : "shortestpath";
});

document.getElementById('alternateBtn').addEventListener('change', function(e) {
    pathMethod = e.target.checked ?  "alternativepath" : "singlepath";
});


MAP.on("click", function (e) {
    clearOldLayers();

    const position = ol.proj.toLonLat(e.coordinate);

    if (counter%2 === 0) {
        clearLayer(secondMarkerLayer);
        FIRST_MARKER.getGeometry().setCoordinates(e.coordinate);
        firstMarkerLayer = createLayerVector([FIRST_MARKER]);
        addLayer(firstMarkerLayer, false);
        firstCoordInput.value = position[0].toFixed(7) + "," + position[1].toFixed(7);
        counter++;
    } else if (counter%2 === 1) {
        SECOND_MARKER.getGeometry().setCoordinates(e.coordinate);
        secondMarkerLayer = createLayerVector([SECOND_MARKER]);
        addLayer(secondMarkerLayer, false);
        secondCoordInput.value = position[0].toFixed(7) + "," + position[1].toFixed(7);
        counter++;
    }
});
/************* --------------------- *************/


/**** METHODS ******/
// Flatpickr ile tarih ve saat seçici
document.addEventListener("DOMContentLoaded", function () {
    flatpickr("#datetime", {
        enableTime: true,
        dateFormat: "Y-m-d H:i:S",
        defaultDate: new Date(),
        time_24hr: true
    });
});

// async function findShortestPath() {
//     clearOldLayers();
//
//     const [lon1, lat1] = firstCoordInput.value.split(",").map(parseFloat);
//     const [lon2, lat2] = secondCoordInput.value.split(",").map(parseFloat);
//
//     // Kullanıcının seçtiği tarih ve saat bilgisi
//     const selectedDateTime = document.getElementById("datetime").value;
//     const dateObj = new Date(selectedDateTime);
//
//     const day = dateObj.getDay(); // Haftanın günü (0 = Pazar, 6 = Cumartesi)
//     const hour = dateObj.getHours().toString().padStart(2, '0');
//     const minute = dateObj.getMinutes().toString().padStart(2, '0');
//     const second = dateObj.getSeconds().toString().padStart(2, '0');
//
//     const start_time = `${day}:${hour}:${minute}:${second}`;
//
//     let url = `${BASE_URL}/shortest-path/?lat1=${lat1}&lon1=${lon1}&lat2=${lat2}&lon2=${lon2}&start_time=${start_time}`;
//
//     console.log("Requesting:", url);
//
//     const res = await fetch(url);
//     const data = await res.json();
//
//     if (routeMethod !== "multimodalroute" && pathMethod === "singlepath") {
//         drawPath(data.path);
//     } else {
//         drawMultiModalPath(data);
//     }
// }
async function findShortestPath() {
    clearOldLayers();

    const [lon1, lat1] = firstCoordInput.value.split(",").map(parseFloat);
    const [lon2, lat2] = secondCoordInput.value.split(",").map(parseFloat);

    const selectedDateTime = document.getElementById("datetime").value;
    const dateObj = new Date(selectedDateTime);

    const day = (dateObj.getDay() - 1) % 7; // weekday (0 = Monday, 6 = Sunday)
    const hour = dateObj.getHours().toString().padStart(2, '0');
    const minute = dateObj.getMinutes().toString().padStart(2, '0');
    const second = dateObj.getSeconds().toString().padStart(2, '0');
    const start_time = `${day}:${hour}:${minute}:${second}`;

    const requestBody = {
        lat1: lat1,
        lon1: lon1,
        lat2: lat2,
        lon2: lon2,
        start_time: start_time
    };

    let url = "";
    if (routeMethod === "multimodalroute") {
        if (pathMethod === "alternativepath") {
            url = `${BASE_URL}/alternative-paths/`;
        } else {
            url = `${BASE_URL}/shortest-path/`;
        }
    } else {
        return alert("Please select 'Multimodal Route' to use this feature. This part is not ready yet.");
    }

    console.log("Requesting:", url, "with body:", requestBody);

    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody)
    });
    const data = await res.json();

    if (routeMethod === "multimodalroute" && pathMethod === "alternativepath") {
         altPaths = data; // data: alternatif rotalar dizisi
         currentAltIndex = 0;
         displayAlternativePath(currentAltIndex);
    } else {
         // Tek rota durumunda
         drawMultiModalPath(data);
}
}
/************* --------------------- *************/

function updateLegend(path) {
    const legendList = document.getElementById("legend-list");
    legendList.innerHTML = "";  // Önce eski içeriği temizle

    const path_ids = path.tags;
    const path_times = path.times;

    // **Her subpath için yeni bir legend item ekle**
    for (let i = 0; i < path_ids.length; i++) {
        let type = path_ids[i][0];  // **Rota tipi (bus, tram, train, walk)**
        let name = path_ids[i][1];  // **Hattın numarası (607, 66, S23, vb.)**
        let timeInfo = path_times[i];  // **Zaman bilgisi [başlangıç, bitiş]**
        let timeText = (timeInfo && timeInfo[0] && timeInfo[1]) ? `${timeInfo[0]} - ${timeInfo[1]}` : timeInfo ? timeInfo[0] : "";

        // **Her rota tipi için uygun ikon ve renk ayarla**
        let icon = "";
        if (type === "bus") icon = "🚌";
        else if (type === "tram") icon = "🚋";
        else if (type === "train") icon = "🚆";
        else if (type === "walk") icon = "🚶";
        else if (type === "transfer") icon = "🔄";

        // **Legend'a yeni bir öğe ekle**
        let listItem = document.createElement("li");
        listItem.classList.add("legend-item");

        listItem.innerHTML = `
            <span>${icon} ${type.charAt(0).toUpperCase() + type.slice(1)} ${name ? name : ""} ${timeText ? `(${timeText})` : ""}</span>
        `;

        legendList.appendChild(listItem);
    }
}
const createTextStyle = (text) => {
    if (!text) return null;  // Eğer text boşsa, style oluşturma.

    return new ol.style.Text({
        text: text,
        font: 'bold 14px Arial',  // **Yazı tipi**
        fill: new ol.style.Fill({ color: 'black' }),  // **Yazı rengi**
        stroke: new ol.style.Stroke({ color: 'white', width: 3 }),  // **Dış çerçeve**
        placement: 'line',  // **Çizgi üzerine yaz**
        maxAngle: 0.7853981633974483,  // **Maksimum açı**
        textAlign: 'center',
        textBaseline: 'middle',
        overflow: true,
        rotation: 0,
        offsetY: -5  // **Çizginin biraz yukarısına alınması için**
    });
};


/* Fonksiyon: Geçerli alternatif rotayı çizdirir ve legend’i günceller */
function displayAlternativePath(index) {
if (!altPaths.length) return;
// Haritayı temizle
clearOldLayers();
// İlgili alternatif rotayı çiz
drawMultiModalPath(altPaths[index]);
}

/* Ok butonlarına event listener ekleyin */
document.getElementById('altPathLeft').addEventListener('click', function () {
if (!altPaths.length) return;
// Sol ok: index’i bir azalt, 0’dan küçükse son alternatife geç
currentAltIndex = (currentAltIndex - 1 + altPaths.length) % altPaths.length;
displayAlternativePath(currentAltIndex);
});

document.getElementById('altPathRight').addEventListener('click', function () {
if (!altPaths.length) return;
// Sağ ok: index’i bir artır, dizinin sonunu aşarsa başa dön
currentAltIndex = (currentAltIndex + 1) % altPaths.length;
displayAlternativePath(currentAltIndex);
});

