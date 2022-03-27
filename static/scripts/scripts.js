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

const LEADERBOARD_SLOT_SIZE = 40;

const LEADERBOARD_OFFSET = 0;

BOTTOM_OF_SCREEN = window.screen.height - 300;

function get_topic_list()
{

    let course = document.getElementById("course").value;
    let offset = 1;
    if (course == "igcse") { source = IGCSE_TOPICS; }
    else if (course == "a2") { source = A2_TOPICS; offset = 40;}

    let topic_checkbox_display = document.getElementById("topic_checkbox_display");

    topic_checkbox_display.innerHTML = '';

    let count = offset
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
        checkbox.setAttribute("index", count)

        label.setAttribute("for", "topic_"+topic_id);
        label.innerHTML = topic;

        topic_checkbox_display.appendChild(checkbox_div);

        count++;

    }


    topic_checkbox_display.innerHTML = topic_checkbox_display.innerHTML + `
                            <label for="q_repeat">Repeat each question </label>

                            <select name="q_repeat" id="q_repeat">
                                <option value="infinity" selected>∞</option>
                                <option value="1">1</option>
                                <option value="2">2</option>
                                <option value="3">3</option>
                                <option value="4">4</option>
                                <option value="5">5</option>
                                <option value="6">6</option>
                                <option value="7">7</option>
                                <option value="8">8</option>
                                <option value="9">9</option>
                                <option value="10">10</option>
                            </select> times.`;

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


function init_leaderboards()
{
    let leaderboard = document.getElementById("overall_leaderboard")
    let i = 1;
    for (let y=0; y+LEADERBOARD_SLOT_SIZE; y<=(LEADERBOARD_SLOT_SIZE*10) )
    {
        let leaderboard_slot = document.createElement("div");
        leaderboard_slot.style.top = y;
        i++;
        leaderboard.appendChild(leaderboard_slot);
    }
}

function update_slot(name, new_pos, pts, leaderboard,table_name)
{

    leaderboard_slot = $(`div[name="${table_name+name}"]`);

    if (leaderboard_slot.length == 0)
    {
        let new_slot = document.createElement("div");
        leaderboard.appendChild(new_slot);
        new_slot.style.top = "inherit";
        new_slot.style.left = "inherit";
        new_slot.setAttribute("name", table_name+name);
        new_slot.classList.add("leaderboard_slot");

        leaderboard_slot = $(`div[name="${table_name+name}"]`);
    }

    let pos = Math.floor(new_pos / LEADERBOARD_SLOT_SIZE) + 1;
    leaderboard_slot.html(`#${pos} ${name} (${pts})`);
    leaderboard_slot.animate({'top': new_pos.toString()+"px"}, 500);
}

function update_leaderboard(table_name, leaderboards_update)
{

    let current_leaderboard = document.getElementById(table_name+"_leaderboard");

    let update = leaderboards_update[table_name];

    console.log(update);

    console.log("Does update have keys")

    console.log(Object.keys(update))

    let holders = [];

    // iterate through existing leaderboard slots and animate
    for (let slot of current_leaderboard.childNodes)
    {
        let current_holder = slot.getAttribute("name")
        let name_only = current_holder.replace(table_name, "")
        if (Object.keys(update).includes(name_only))
        {
            console.log("new position: " + current_holder)

            new_pos = LEADERBOARD_OFFSET + (update[name_only][0] * LEADERBOARD_SLOT_SIZE);
            let pts = update[name_only][1];
            update_slot(name_only, new_pos, pts, current_leaderboard, table_name);
            holders.push(name_only);
        }
        else
        {
            console.log("No longer on the leaderboard: " + current_holder)
            $(`div[name="${table_name+current_holder}"]`).animate({'top': BOTTOM_OF_SCREEN.toString()+"px"}, 500);
            current_leaderboard.removeChild(slot);
        }
    }

    console.log("look at holders")

    console.log(holders)

    // iterate through any new leaderboard slots and add in
    for (let [this_person, row] of Object.entries(update))
    {
        if (holders.includes(this_person)) { continue };

        new_pos = LEADERBOARD_OFFSET + (row[0] * LEADERBOARD_SLOT_SIZE);
        let pts = row[1];

        console.log("Animate to ", new_pos);
        console.log("Found " + this_person + "who is not in the leaderboard");

        update_slot(this_person, new_pos, pts, current_leaderboard, table_name);

    }




}

function animate_feedback(fb_anim, data)
{
    console.log("feedback anim");
    console.log(fb_anim);
    if (fb_anim != -1) { anim_actions = {"top":fb_anim.toString(), "opacity":0} }
    else { anim_actions = {"left":"1000", "opacity":0} };

    let fb =$("#feedback")

    fb.css({"opacity":1, "top":"200px"});
    fb.show();
    fb.fadeOut(0);
    fb.fadeIn(1000,
        () => $("#question").html(data.next_question).fadeIn(100,
            () => fb.animate(anim_actions, 1000,  () => fb.hide()
            )
        )
    );



}


function process_hints(hints)
{
    for (let h of hints)
    {
         let new_hint = document.createElement("div")
         new_hint.innerHTML = h.text;
         new_hint.classList.add("hint")
         new_hint.style.top = h.y.toString() + "px";
         new_hint.style.left = ((window.screen.width * (1/6)) + h.x).toString() + "px";
         new_hint.style.color = h.colour;
         document.getElementsByTagName("body")[0].appendChild(new_hint);

         new_hint.opacity = 1;

        $(new_hint).fadeOut(5000, function() {
            $(this).remove();
        });
    }
}

function remove_hints()
{
    let body = document.getElementsByTagName("body")[0];

    for (let hint of document.getElementsByClassName("hint"))
    {
        body.removeChild(hint);
    }
}

function process_feedback(feedback, scores)
{

    console.log("Feedback is");
    console.log(feedback);
    feedback_div = document.getElementById("feedback");
    question_div = document.getElementById("question");

    feedback_div.innerHTML = "";

    for (let child of question_div.childNodes)
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
    else if (average(scores) == 0) { return BOTTOM_OF_SCREEN }
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


    update_score(data.total);

    update_leaderboard("overall", data.leaderboards);
    update_leaderboard("last_hour", data.leaderboards);


    animate_feedback(fb_anim, data);


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
        if (t.checked) { selected_topics.push(t.getAttribute("name"))}
    }
    form_data.append("selected_topics", selected_topics);
    form_data.append("q_repeat", document.getElementById("q_repeat").value);
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