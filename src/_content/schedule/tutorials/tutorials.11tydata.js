let data = {
  layout: "tutorial-details.html",
};


if(process.env.NODE_ENV === "production") {
  data.date = "git Last Modified";
}

module.exports = data;
