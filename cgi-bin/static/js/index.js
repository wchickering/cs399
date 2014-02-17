var currentProduct=new Object();
var defaultId = 1082639;

// Set currentProduct initially to have smallest id
var firstId = getIdFromURL();
getNextProduct(firstId, "first");

function getIdFromURL() {
    var name = "firstId";
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results == null ? defaultId : decodeURIComponent(results[1].replace(/\+/g, " "));
}

function changeProduct(product) {
    image = document.getElementById("productImage");
    link = document.getElementById("productLink");
    image.setAttribute("src", "static/" + product.ImgFile);
    link.setAttribute("href", "http://www.macys.com/" + product.Url);
}

function createImageNode() {
    var smallImage=document.createElement("img");
    smallImage.setAttribute("src", "static/" + currentProduct.ImgFile);
    smallImage.setAttribute("class", "img-thumbnail");
    smallImage.setAttribute("id", "smallImage");
    return smallImage;
}

function addToList(list) {
    var smallImage = createImageNode();
    var list=document.getElementById(list);
    list.appendChild(smallImage);
}

function writeToTest() {
    var test = document.getElementById("test");
    test.innerHTML = "This is just a test";
}

function getNextProduct(productId, liked) {
    $.post("/leftorright", 
            {
                'productId':productId,
    'liked':liked
            },
            function(data,status){
                var product = JSON.parse(data);
                document.getElementById("test").innerHTML = "Id = " + product.Id +
        ", Description = " + product.Description;
    changeProduct(product);
    currentProduct = product;
            });
}

function move(list) {
    addToList(list);
    getNextProduct(currentProduct.Id, list);
}

$(document).keyup(function(e) {
    if (e.keyCode == 49) { 

        move("disliked");
    }
    else if (e.keyCode == 50) {

        move("liked");
    }
});



