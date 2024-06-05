$(function () {
  console.log("in js");

  $('.searchButton').on('click', function () {
    var title = $('.movie').val();
    console.log("clicked")
    window.location.href = "/home/" + title


  });

  
    $(".star").on("mouseover", function () { //SELECTING A STAR
      $(".rating").hide(); //HIDES THE CURRENT RATING WHEN MOUSE IS OVER A STAR
      var d = $(this).attr("id"); //GETS THE NUMBER OF THE STAR

      //HIGHLIGHTS EVERY STAR BEHIND IT
      for (i = (d - 1); i >= 0; i--) {
        $(".transparent .star:eq(" + i + ")").css({ "opacity": "1.0" });
      }
    }).on("click", function () { //RATING PROCESS
      var movieId = $("#movieID").val(); //GETS THE ID OF THE CONTENT
      var rating = $(this).attr("id"); //GETS THE NUMBER OF THE STAR
      console.log("id is"+movieId)

      $.ajax({
        method: "POST",
        contentType: 'application/json;charset=UTF-8',
        data: JSON.stringify({ 'movieId': movieId, 'rating': rating }),
        url: "/rate", //CALLBACK
        success: function (e) {
          var stars = '';

          for (var i = 1; i <= e.vote_rate; i++) {
            stars += '<div class="star" id="' + i + '"></div>';
          }

          var str = '<div class="r"><div class="rating">' + stars + '<div>Rating: '+e.vote_rate+'</div></div>'

          $("#ajax_vote").html(str); //DISPLAYS THE NEW RATING IN HTML
        },
        error: function (e) {
          console.log(e);
        }
      });
    }).on("mouseout", function () { //WHEN MOUSE IS NOT OVER THE RATING
      $(".rating").show(); //SHOWS THE CURRENT RATING
      $(".transparent .star").css({ "opacity": "0.25" }); //TRANSPARENTS THE BASE
    });
})
function recommendcard(e) {
  var id = e.getAttribute('id');
  window.location.href = "/recommend/" + id

}

