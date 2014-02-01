var count = 0;
var productIdCount = 0;
var productIds=new Array();
productIds[0] = 48;
productIds[1] = 1376503;
var products=new Array();
products[0]={name:'Name1', image:'lorempixel.people.1.jpeg', id:'product1', url:'http://www.google.com/search?q=1'};
products[1]={name:'Name2', image:'lorempixel.city.1.jpeg', id:'product2', url:'http://www.google.com/search?q=2'};
products[2]={name:'Name3', image:'lorempixel.technics.1.jpeg', id:'product3', url:'http://www.google.com/search?q=3'};
products[3]={name:'Name4', image:'lorempixel.abstract.1.jpeg', id:'product4', url:'http://www.google.com/search?q=4'};
products[4]={name:'Name5', image:'lorempixel.abstract.8.jpeg', id:'product5', url:'http://www.google.com/search?q=5'};
var currentProduct=products[0];

function getNextProduct() {
    if (count < products.length - 1) {
        count++;
    }
    return products[count];
}

function changeProduct() {
    var nextProduct = getNextProduct();
    paragraph = document.getElementById("productName");
    image = document.getElementById("productImage");
    link = document.getElementById("productLink");
    image.setAttribute("src", "../static/images/" + nextProduct.image);
    link.setAttribute("href", nextProduct.url);
    // update current product
    currentProduct = nextProduct;
}

function createImageNode() {
    var smallImage=document.createElement("img");
    smallImage.setAttribute("src", "../static/images/" + currentProduct.image);
    smallImage.setAttribute("class", "img-thumbnail");
    smallImage.setAttribute("id", "smallImage");
    return smallImage;
}

function addToList(list) {
    var smallImage = createImageNode();
    var list=document.getElementById(list);
    list.appendChild(smallImage);
}

function addRight() {
    var smallImage = createImageNode();
    var likedList=document.getElementById("liked");
    likedList.appendChild(smallImage);
}

function getPythonOutput() {
    $.ajax({
        url: "~/Desktop/cs399/cs399/macys/test.py",
    data: 5,
    success: function(data) {
        var test = document.getElementById("test");
        test.innerHTML = "Test results = " + data;
    }
    });
}

function writeToTest() {
    var test = document.getElementById("test");
    test.innerHTML = "This is just a test";
}

function postForm() {
    // Create form
    var form = document.createElement('form');
    form.setAttribute('method', 'post');
    form.setAttribute('action', '/leftorright');
    // create input child
    var hiddenField = document.createElement('input');
    hiddenField.setAttribute('type', 'hidden');
    hiddenField.setAttribute('name', 'productId');
    hiddenField.setAttribute('value', productIds[productIdCount]);
    // add child to form and submit
    form.appendChild(hiddenField);
    document.body.appendChild(form);
    form.submit();
    // increase to the next product
    productIdCount++;
}

function loadXMLDoc()
{
    var xmlhttp;
    if (window.XMLHttpRequest)
    {// code for IE7+, Firefox, Chrome, Opera, Safari
        xmlhttp=new XMLHttpRequest();
    }
    else
    {// code for IE6, IE5
        xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.onreadystatechange=function()
    {
        if (xmlhttp.readyState==4 && xmlhttp.status==200)
        {
            document.getElementById("test").innerHTML=xmlhttp.responseText;
        }
    }
    xmlhttp.open("GET","ajax_info.txt",true);
    xmlhttp.send();
}

function move(list) {
    addToList(list);
    changeProduct();
    postForm();
    //getPythonOutput();
    //writeToTest();
}

$(document).keyup(function(e) {
    if (e.keyCode == 49) { 
        move("disliked");
    }
    else if (e.keyCode == 50) {
        move("liked");
    }
});

