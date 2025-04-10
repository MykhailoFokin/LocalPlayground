from airflow.operators.email import EmailOperator

class CustomEmailOperator(EmailOperator):
    def render_template_fields(self, context, jinja_env = None):
        """Overridden method to parse task's `params` attribute with Jinja.
        """
        # Check if `params` is a dict or a ParamsDict object
        if isinstance(self.params, dict):
            context['params'] = self.render_template(self.params, context, jinja_env, set())
        else:
            context['params'] = self.render_template(self.params.dump(), context, jinja_env, set())          
        # Call parent's method
        super().render_template_fields(context, jinja_env)