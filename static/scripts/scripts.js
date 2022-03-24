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

    let checkboxes = "";



    for (let topic of source)
    {
        topic_id = topic.split(" ");
        topic_id = topic_id.slice(1, topic.length);
        topic_id = topic_id.join("").replace(" ", "_").toLowerCase();

        checkboxes += `<div class="topic_checkbox"><input type="checkbox" id="${topic_id}" name="${topic_id}" checked>  <label for="${topic_id}">${topic}</label></div>`;


    }

    topic_checkbox_display.innerHTML = checkboxes;


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

    function get_question()
	{
		fetch('/get_question')
		.then(res => {
    	return res.text()})
		.then(data => {
		$('#stats_modal_header').html('<h4 class="modal-title">' + JSON.parse(data).display_name + "'s Stats</h4>");
		$('#stats_modal_content').html(JSON.parse(data).stats);

    	}
    	);
    };

    function submit_answer()
	{
		console.log("reporting problem");
		let form_data = new FormData();
		form_data.append('q_num', $("input#q_num").val());

		console.log(form_data);

		fetch('/submit_answer',
		{
			body:form_data,
			method:"post"
		})
		.then(res => {
    	return res.text()})
		.then(data => {
		 $('#report_problem_modal').modal('toggle');
		//$('#msgs').html(data).show().delay(3000).fadeOut(3000);
		$('#msgs').append(data);
    	}
    	);

    };


