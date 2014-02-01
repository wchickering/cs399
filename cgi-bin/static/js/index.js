var currentProduct=new Object();
// Set currentProduct initially to have smalled id
$.post("/leftorright", 
        {
            productId:0
        },
        function(data,status){
            var product = JSON.parse(data);
            document.getElementById("test").innerHTML = "Id = " + product.Id +
                ", Description = " + product.Description;
            currentProduct = product;
            changeProduct(product);
        });


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

function JQAjax() {
    $.post("/leftorright", 
            {
                productId:currentProduct.Id
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
    JQAjax();
}

$(document).keyup(function(e) {
    if (e.keyCode == 49) { 

        move("disliked");
    }
    else if (e.keyCode == 50) {

        move("liked");
    }
});



