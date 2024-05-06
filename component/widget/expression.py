import ipyvuetify as v
from ipywidgets import Output, HTMLMath
from collections import defaultdict
from component.model.benefit_model import BenefitModel
from component.frontend.remath import remath
from component.widget.buttons import IconBtn


class ExpressionBtn(v.Flex):
    def __init__(self, benefit_model, **kwargs):
        # to align the flex container to the right
        self.style_ = "flex: 0"

        super().__init__(**kwargs)

        self.color = "primary"
        self.snack = ExpressionDialog(benefit_model)
        btn = IconBtn("fa-solid fa-circle-info")
        self.children = [btn, self.snack]

        btn.on_event("click", self.show_snack)
        self.snack.remath.remath()

    def show_snack(self, *args):

        self.snack.v_model = True
        self.snack.remath.remath()


class ExpressionDialog(v.Dialog):
    def __init__(self, benefit_model: BenefitModel, **kwargs):
        super().__init__(**kwargs)
        self.benefit_model = benefit_model

        self.v_model = False
        self.remath = remath
        self.width = 780

        wabi = r"$$wabi = \frac{\sum_{t=1}^n W_t B_t}{\sum_{t=1}^n W_t};$$"
        Wt_Bt = (
            r"$$Wt = \frac{\sum_{i=1}^m w_i}{m}; Bt = \frac{\sum_{i=1}^m b_i}{m};$$ "
        )
        WtBt = r"$$ W_t \times B_t = \left( \frac{\sum_{i=1}^m w_i}{m} \right) \times \left( \frac{\sum_{i=1}^m b_i}{m} \right) = \frac{\sum_{i=1}^m w_i * b_j}{m^2} $$"
        # WtBt = r"$$ W_t \times B_t = \left( \frac{\sum_{i=1}^m w_i}{m} \right) \times \left( \frac{\sum_{i=1}^m b_i}{m} \right) = \frac{\sum_{i=1}^m w_i \sum_{j=1}^m b_j}{m^2} $$"

        # display()

        # Example usage:
        benefits = rename_benefits(benefit_model.themes)
        weights = benefit_model.weights
        self.wabi_expanded_expression = Expression(expand_wabi(benefits, weights))

        btn_close = IconBtn(gliph="mdi-close")
        self.children = [
            v.Card(
                width=780,
                children=[
                    v.CardTitle(
                        children=[
                            "Weighted Average Index calculation",
                            v.Spacer(),
                            btn_close,
                        ]
                    ),
                    v.CardText(
                        class_=".text-decoration-line-through body-2",
                        children=[
                            v.Flex(children=[Expression(wabi)], height="189px"),
                            v.Flex(children=[Expression(Wt_Bt)], height="189px"),
                            v.Flex(children=[Expression(WtBt)], height="189px"),
                            v.Flex(
                                children=[self.wabi_expanded_expression], height="189px"
                            ),
                            v.VuetifyTemplate(
                                template="""
                                <style sepal-ui-script>
                                    .expression {
                                        background-color: inherit;
                                        color: inherit !important;
                                    }
                                    .expression .MathJax {
                                        font-size: 22px !important;
                                    }
                                    .expression .widget-htmlmath-content {
                                        font-size: 22px !important;
                                    }
                                </style>
                                """
                            ),
                        ],
                    ),
                ],
            )
        ]

        btn_close.on_event("click", lambda *args: setattr(self, "v_model", False))
        benefit_model.observe(self.update_expression, "new_changes")

    def update_expression(self, _):
        wabi = expand_wabi(
            rename_benefits(self.benefit_model.themes), self.benefit_model.weights
        )
        self.wabi_expanded_expression.update(wabi)
        self.remath.remath()


class ExpressionTemplate:

    def __init__(self, content):
        self.add_class("expression")
        self.update(content)


class Expression(HTMLMath, ExpressionTemplate):

    def __init__(self, content):
        super().__init__(content=content)

    def update(self, content):
        """Update the content of the expression replacing the previous"""
        self.value = content


class ExpressionOutput(Output, ExpressionTemplate):

    def __init__(self, content):
        super().__init__(content=content)

    def update(self, content):
        """Update the content of the expression replacing the previous"""
        self.outputs = (
            {
                "output_type": "display_data",
                "data": {
                    "text/plain": "<IPython.core.display.Markdown object>",
                    "text/markdown": content,
                },
            },
        )


def rename_benefits(item_list):
    unique_items = {}
    output_list = []
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    current_index = 0  # Start at the first letter of the alphabet

    for item in item_list:
        if item not in unique_items:
            # Assign a new letter from the alphabet to new items
            unique_items[item] = alphabet[current_index]
            current_index += 1  # Move to the next letter for the next new item
        # Append the assigned letter to the output list
        output_list.append(unique_items[item])

    return output_list


def expand_wabi(benefit_names, weights):
    if len(benefit_names) != len(weights):
        return "Error: The length of benefit names and weights must match."

    # Grouping weights by benefit name
    weight_groups = defaultdict(list)
    benefit_indices = defaultdict(int)

    for name, weight in zip(benefit_names, weights):
        benefit_indices[name] += 1
        weight_groups[name].append(weight)

    # Building LaTeX expressions for each group
    WtBt_expressions = []
    Wt_expressions = []

    for name in sorted(weight_groups.keys()):
        num_entries = len(weight_groups[name])
        indices = range(1, num_entries + 1)

        if num_entries > 1:
            name_expr = f"\\left(\\frac{{{' + '.join(f'{name}_{{{i}}}' for i in indices)}}}{{{num_entries}}}\\right)"
            Wt_expr = f"\\left(\\frac{{{' + '.join(map(str, weight_groups[name]))}}}{{{num_entries}}}\\right)"
        else:
            name_expr = f"{name}_1"
            Wt_expr = str(weight_groups[name][0])

        WtBt_expressions.append(f"({Wt_expr} \\times {name_expr})")
        Wt_expressions.append(Wt_expr)

    # Joining the expressions with "+" for sum in LaTeX style
    sum_WtBt = " + ".join(WtBt_expressions)
    sum_Wt = " + ".join(Wt_expressions)

    # Generating the full wabi formula in LaTeX notation
    wabi_formula = f"$$wabi = \\frac{{{sum_WtBt}}}{{{sum_Wt}}}$$"
    return wabi_formula
