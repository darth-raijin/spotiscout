function addRow() {
    // Insert another columns row, with proper fields
    $("#budgetform").append(
        '<div class="columns budget-columns"> \n ' +
        '<input type="hidden" class="id" name="id" id="id" value="new"> \n' +
        '<div class="column">\n' +
        '<label for="Amount"><b>Amount</b></label> \n' +
        '<input class="input amount" type="number" id="amount" pattern="/^[0-9]*(.[0-9]{0,2})?$/" \n' +
        'title="Only positive numbers, with period (.) as a delimiter. Example: 100 or 100.25" id="amount" placeholder="Enter amount" required> \n' +
        "</div>\n" +
        '<div class="column select is-fullwidth"> \n' +
        '<label for="type"><b>Type</b></label> \n' +
        '<select id="type" class="type" required> \n' +
        '<option value="incomes" selected>Incomes</option> \n' +
        '<option value="expenses">Expenses</option> \n' +
        '<option value="investments">Investments</option> \n' +
        '<option value="savings">Savings</option> \n' +
        "</select> \n" +
        "</div> \n" +
        '<div class="column"> \n' +
        '<label for="category"><b>Category</b></label> \n' +
        '<input class="input category" type="text" id="category" placeholder="Enter category for item" required> \n' +
        "</div> \n" +
        '<div class="column">\n' +
        '<label for="category"><b>Delete Row</b></label>\n' +
        '<button class="button is-fullwidth is-danger delete-row" type="button" onclick="deleteRow()">Delete</button>\n' +
        "</div>\n" +
        "</div>\n"
    );
}

function deleteRow() {
    $(document).on("click", ".delete-row", function (e) {
        e.preventDefault();
        $(this).closest(".columns").remove();
        console.log("Removed column");
        return false;
    });
}

function postBudget() {
    $(".post-budget").click(function (event) {
        console.log("PostMan!");
        event.preventDefault();

        // Validate fields to ensure value is present
        document.querySelectorAll(".amount").forEach(function (el) {
            if (el.value == "") {
                return alert("Remember to fill out all amounts!");
            }

            // Convert String in input to number, and set fraction digits
            var currentAmount = Number(el.value);
            el.value = currentAmount.toFixed(2);
        });

        document.querySelectorAll(".category").forEach(function (el) {
            if (el.value == "") {
                return alert("Remember to fill out all categories!");
            }
        });

        // JSON for holding form data
        let data = { new: [] };
        let id, amount, category, type;
        let columns = document.querySelectorAll(".budget-columns");

        columns.forEach(function (el) {
            console.log(columns);
            // Fetching input field values and setting to keys
            id = el.querySelector(".id").value;
            amount = el.querySelector(".amount").value;
            category = el.querySelector(".category").value;
            type = el.querySelector(".type").value;

            // Create JSON object and append to data-variable
            if (id === "new") {
                data["new"].push({
                    amount: Number(amount),
                    category: category,
                    type: type,
                });
            } else {
                data[id.toString()] = {
                    amount: amount,
                    category: category,
                    type: type,
                };
            }
        });

        fetch("http://localhost:5000/dash/budget/edit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(data),
        })
            .then((response) => response.json)
            .then((data) => {
                console.log('Success:', data)
            })
            .catch((error) => {
                console.error("Error:", error);
            });
    });
}
