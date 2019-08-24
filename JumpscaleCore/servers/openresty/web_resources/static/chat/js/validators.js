function validate(value, validators) {
    // For every validation key, validate with the corresponding function
    let errors = []
    for (let key in validators){
        if (window["validate_"+key]){
            error = window["validate_"+key](value, validators[key]);
            if (error){
                errors.push(error);
            }
        }
    }
    return errors
}

function validate_required(value){
    //Validate non empty values
    if (!value) {
        return "This field is required";
    }
    return null;
}

function validate_jwt(value){
    //Basic validation of jwt structure
    try{
        //Parse JWT to its components
        var base64Url = value.split('.')[1];
        var base64 = base64Url.replace('-', '+').replace('_', '/');
        var parsed_jwt =  JSON.parse(window.atob(base64));
    }
    catch(err){
        //If JWT fails to parse then the it is not valid
        console.log(err);
        return "Invalid JWT";
    }
    return null 
}


function validate_email(value){
    //Validate a valid email structure
    var emailformat = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,4})+$/;
    if(!emailformat.test(value.toLowerCase())){
        return "This field should be an email"
    }
    return null;
}


function validate_string(value){
    //Validate value is a String
    if (typeof value !== 'string'){
        return "This field should include text"
    }
    return null;
}

function validate_number(value){
    //Validate input consists of numbers only
    if (!$.isNumeric(value)){
        return "This field should be a number"
    }
    return null;
}

function validate_length(value,validator){
    //Validate value has a certain length
    if(value.length !== validator){
        return "The length of this field should be " + validator
    } 
    return null; 
}

function validate_length_min(value,validator){
    //Validate value has a certain minimum length
    if(value.length < validator){
        return "The length of this field should be at least " + validator
    } 
    return null; 
}

function validate_length_max(value,validator){
    //Validate value has a certain maximum length
    if(value.length > validator){
        return "The length of this field should be less than " + validator
    } 
    return null; 
}

function validate_min(value,validator){
    //Validate value is greater than or equal a certain minimum value
    if(value && Number(value)<validator){
        return "This field should be at least " + validator;
    }
    return null;
}

function validate_max(value,validator){
    //Validate value is less than or equal a certain maximum value
    if(value && Number(value)>validator){
        return "This field should be less than " + validator;
    }
    return null;
}

function validate_github_url_https(value){
    //Validate github repo url is https format
    var url_format = /^https\:\/\/github\.com\/\S+\/\S+/;
    if(!url_format.test(value)){
        return "This field should be in the following format : https://github.com/Owner/repo_name";
    }
    return null;
}