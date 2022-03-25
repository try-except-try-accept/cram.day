IGCSE_TOPICS = `3.1.1 REPRESENTING ALGORITHMS
3.1.2 EFFICIENCY OF ALGORITHMS
3.1.3 SEARCHING ALGORITHMS
3.1.4 SORTING ALGORITHMS
3.2.1 DATA TYPES
3.2.2 PROGRAMMING CONCEPTS
3.2.3 ARITHMETIC OPERATIONS IN A PROGRAMMING LANGUAGE
3.2.4 RELATIONAL OPERATIONS IN A PROGRAMMING LANGUAGE
3.2.5 BOOLEAN OPERATIONS IN A PROGRAMMING LANGUAGE
3.2.6 DATA STRUCTURES
3.2.7 INPUT/OUTPUT AND FILE HANDLING
3.2.8 STRING HANDLING OPERATIONS IN A PROGRAMMING LANGUAGE
3.2.9 RANDOM NUMBER GENERATION IN A PROGRAMMING LANGUAGE
3.2.10 SUBROUTINES (PROCEDURES AND FUNCTIONS)
3.2.11 STRUCTURED PROGRAMMING
3.2.12 ROBUST AND SECURE PROGRAMMING
3.2.13 CLASSIFICATION OF PROGRAMMING LANGUAGES
3.3.1 NUMBER BASES
3.3.2 CONVERTING BETWEEN NUMBER BASES
3.3.3 UNITS OF INFORMATION
3.3.4 BINARY ARITHMETIC
3.3.5 CHARACTER ENCODING
3.3.6 REPRESENTING IMAGES
3.3.7 REPRESENTING SOUND
3.3.8 DATA COMPRESSION
3.4.1 HARDWARE AND SOFTWARE
3.4.2 BOOLEAN LOGIC
3.4.3 SOFTWARE CLASSIFICATION
3.4.4 SYSTEMS ARCHITECTURE
3.5 COMPUTER NETWORKS
3.6.1 CYBER SECURITY THREATS
3.6.1.1 SOCIAL ENGINEERING
3.6.1.2 MALICIOUS CODE
3.6.2 METHODS TO DETECT AND PREVENT CYBER SECURITY THREATS
3.7.1 RELATIONAL DATABASES
3.7.2 DATABASE DESIGN
3.7.3 STRUCTURED QUERY LANGUAGE (SQL)
3.8.1 WEB PAGE DESIGN KEY CONCEPTS
3.8.2 HYPERTEXT MARKUP LANGUAGE (HTML)`.split("\n")

A2_TOPICS = `13.1 User-defined data types
13.2 File organisation and access
13.3 Floating-point numbers, representation and manipulation
14.1 Protocols
14.2 Circuit switching, packet switching
15.1 Processers, Parallel Processing and Virtual Machines
15.2 Boolean Algebra and Logic Circuits
16.1 Purposes of an Operating System (OS)
16.2 Translation Software
17.1 Encryption, Encryption Protocols and Digital certificates
18.1 Artificial Intelligence
19.1 Algorithms
19.2 Recursion
20.1 Programming Paradigms
20.2 File Processing and Exception Handling`.split("\n")


function get_topic_list()
{

    let course = document.getElementById("course").value;

    if (course == "igcse") { source = IGCSE_TOPICS; }
    else if (course == "a2") { source = A2_TOPICS; }

    let topic_checkbox_display = document.getElementById("topic_checkbox_display");

    topic_checkbox_display.innerHTML = '';

    for (let topic of source)
    {
        topic_id = topic.split(" ");
        topic_index = topic_id[0];
        topic_id = topic_id.slice(1, topic.length);
        topic_id = topic_id.join("").replace(" ", "_").toLowerCase();

        //checkboxes += `<div class="topic_checkbox"><input type="checkbox" class="topic_checkbox" id="topic_${topic_id}" name="topic_${topic_index}" checked>  <label for="topic_${topic_id}">${topic}</label></div>`;


        let checkbox_div = document.createElement("div");
        let checkbox = document.createElement("input");
        let label = document.createElement("label");

        checkbox_div.appendChild(checkbox);
        checkbox_div.appendChild(label);

        checkbox.setAttribute("type", "checkbox");
        checkbox.setAttribute("class", "topic_checkbox");
        checkbox.setAttribute("checked", true);
        checkbox.setAttribute("name", topic_index);
        checkbox.setAttribute("id", "topic_"+topic_id);
        label.setAttribute("for", "topic_"+topic_id);
        label.innerHTML = topic;

        topic_checkbox_display.appendChild(checkbox_div);

    }


}


function get_stats()
{
    fetch('/get_stats')
    .then(res => {
    return res.text()})
    .then(data => {
    $('#stats_modal_header').html('<h4 class="modal-title">' + JSON.parse(data).display_name + "'s Stats</h4>");
    $('#stats_modal_content').html(JSON.parse(data).stats);

    }
    );
};


function update_score(score)
{
    document.getElementById("score_display").innerHTML = score;
}


function process_hints(hints)
{
    for (let h of hints)
    {
         let new_hint = document.createElement("div")
         new_hint.innerHTML = h.text;
         new_hint.classList.add("hint")
         new_hint.style.top = h.y.toString() + "px";
         new_hint.style.left = h.x.toString() + "px";
         new_hint.style.color = h.colour;

         document.getElementsByTagName("body")[0].appendChild(new_hint);
    }
}

function remove_hints()
{
    let body = document.getElementsByTagName("body")[0];

    $('.hint').each(function(i, obj)
    {
        let option = Math.floor(Math.random() * 10);

        if (option > 7) { this.animate({"top":"0"}, 1000, () => this.fadeOut(100)) }
        else if (option > 5) { this.animate({"top":"1000px"}, () => this.fadeOut(100) )}
        else if (option > 2) { this.animate({"left":"1000px"}, () => this.fadeOut(100) )}
        else  { this.animate({"top":"1000px", "left":"1000px"}, () => this.fadeOut(100)) } ;
    });
}

function process_feedback(feedback, scores)
{

    console.log("Feedback is");
    console.log(feedback);
    feedback_div = document.getElementById("feedback");
    question_div = document.getElementById("question");

    feedback_div.innerHTML = "";

    for (let child of question_div.childNodes
    )
    {
        let new_node = child.cloneNode()
        try
        {
            if (child.getAttribute("class") == "gap_textfield")
            {

                let next_correct = feedback.pop(0);
                console.log("next correct" + next_correct);
                let text_input_feedback = "";
                if (next_correct != null)
                {
                   text_input_feedback = "✘" + child.value + "✔" + next_correct;

                }
                else
                {
                   text_input_feedback = "✔" + child.value;
                }

                new_node.value = text_input_feedback;

            }
        }
        catch (e) { console.log("problemmm" + e)}

        feedback_div.appendChild(new_node);
    }

    for (let i=0; i<feedback_div.children.length; i++)
    {
        let element = feedback_div.children[i];
        let grading = scores[i];

        element.setAttribute("disabled", true);
        let colour = "incorrect";
        if (grading) { colour = "correct"}
        element.classList.add(colour);
    }


    const average = array => array.reduce( ( p, c ) => p + c, 0 ) / array.length;


    if (average(scores) == 1) { return 0 }
    else if (average(scores) == 0) { return 1000 }
    else { return -1}




}

function submit_answer()
{
    let form_data = new FormData();
    answers = document.getElementsByClassName("gap_textfield");
    answers_given = [];
    for (let a of answers)
    {
        answers_given.push(a.value);
    }
    form_data.append("answers", answers_given);

    fetch('/submit_answer',
    {
        body:form_data,
        method:"post"
    })
    .then(res => {
    return res.json()})
    .then(data => {



    console.log("Received data");
    console.log(data);
    remove_hints();
    let fb_anim = process_feedback(data.feedback, data.scores);
    console.log("feedback anim");
    console.log(fb_anim);
    if (fb_anim != -1) { anim_actions = {"top":fb_anim.toString(), "opacity":0} }
    else { anim_actions = {"left":"1000", "opacity":0} };


    update_score(data.total);


    $("#feedback").css({"opacity":1, "left":"0px", "top":"200px"});
    $("#feedback").fadeOut(0);
    $("#feedback").fadeIn(1000,
        () => $("#question").html(data.next_question).fadeIn(100,
            () => $("#feedback").animate(anim_actions, 1000, () => null)
        )
    );

    }
    );
};


function get_question()
{
    let form_data = new FormData();
    topics = document.getElementsByClassName("topic_checkbox");
    selected_topics = [];
    for (let t of topics)
    {
        if (t.checked) { selected_topics.push(t.name)}
    }
    form_data.append("selected_topics", selected_topics);
    console.log(form_data);

    fetch('/get_question',
    {
        body:form_data,
        method:"post"
    })
    .then(res => {
    return res.text()})
    .then(data => {
     $('#choose_topics_modal').modal('toggle');

    document.getElementById("question").innerHTML = data;

    }
    );
};

function get_hints()
{
    fetch('/get_hints')
    .then(res => {
    return res.json()})
    .then( data => process_hints(data));
};