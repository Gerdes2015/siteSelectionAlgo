import pandas as pd
from pyomo.environ import *

def mip_optimization_with_data(file_path):
    # Load data from the spreadsheet
    data = pd.read_csv(file_path)

    properties = data['Property']
    owners = data['Owner']
    managers = data['Manager']
    timezones = data['Timezone']
    waves = ['Wave1', 'Wave2', 'Wave3', 'Wave4', 'Wave5', 'Wave6', 'Wave7', 'Wave8', 'Wave9', 'Wave10', 'Wave11', 'Wave12', 'Wave13']

    # Model
    model = ConcreteModel()

    # Sets
    model.Properties = Set(initialize=properties)
    model.Waves = Set(initialize=waves)

    # Parameters
    max_properties_per_wave = {'Wave1':5, 'Wave2':45, 'Wave3':150, 'Wave4':300, 'Wave5':350, 'Wave6':20, 'Wave7':400, 'Wave8':45, 'Wave9':400, 'Wave10':5, 'Wave11':400, 'Wave12':350, 'Wave13':350}
    max_owner_per_wave = 15
    max_manager_per_wave = 8
    max_timezone_diff = 4

    # Decision variables
    model.Assign = Var(model.Properties, model.Waves, domain=Binary)

    # Slack variables for soft constraints
    model.OwnerSlack = Var(model.Waves, domain=NonNegativeReals)
    model.ManagerSlack = Var(model.Waves, domain=NonNegativeReals)
    model.maxWaveSlack = Var(model.Waves, domain=NonNegativeReals)

    # Objective: Minimize penalties for owner and manager and max wave size violations
    penalty_owner = 10
    penalty_manager = 15
    penalty_maxWave = 500
    model.Objective = Objective(
        expr=sum(penalty_owner * model.OwnerSlack[w] for w in model.Waves) +
             sum(penalty_manager * model.ManagerSlack[w] for w in model.Waves) +
             sum(penalty_maxWave * model.maxWaveSlack[w] for w in model.Waves),
        sense=minimize
    )

    # Constraints

    # Each property assigned to exactly one wave
    def property_assignment_rule(model, p):
        return sum(model.Assign[p, w] for w in model.Waves) == 1
    model.PropertyAssignment = Constraint(model.Properties, rule=property_assignment_rule)

    # Timezone difference constraint (hard)
    def timezone_diff_rule(model, w):
        assigned_properties = [p for p in model.Properties if model.Assign[p, w].value == 1]
        if len(assigned_properties) < 2:
            return Constraint.Skip
        min_tz = min(timezones[properties.tolist().index(p)] for p in assigned_properties)
        max_tz = max(timezones[properties.tolist().index(p)] for p in assigned_properties)
        return max_tz - min_tz <= max_timezone_diff
    model.TimezoneDiff = Constraint(model.Waves, rule=timezone_diff_rule)

    # Soft constraints: Owner and manager and wave limits with corrected indices
    def owner_constraint_rule(model, w):
        for p in model.Properties:
            if data.loc[data['Property'] == p, 'Owner'].empty:
                raise ValueError(f"No owner found for property {p}. Check your dataset!")
        return sum(model.Assign[p, w] for p in model.Properties) <= max_owner_per_wave + model.OwnerSlack[w]

    model.OwnerConstraint = Constraint(model.Waves, rule=owner_constraint_rule)

    def manager_constraint_rule(model, w):
        return sum(model.Assign[p, w] for p in model.Properties
               if p in data['Property'].values and
               (not pd.isna(data.loc[data['Property'] == p, 'Manager'].values[0]))) <= max_manager_per_wave + model.ManagerSlack[w]

    model.ManagerConstraint = Constraint(model.Waves, rule=manager_constraint_rule)

    # No more than max_properties_per_wave in a wave with slack limit
    max_slack_limit = 50
    def wave_capacity_soft_rule(model, w):
        return sum(model.Assign[p, w] for p in model.Properties) <= max_properties_per_wave[w] + model.maxWaveSlack[w]

    model.maxWaveConstraint = Constraint(model.Waves, rule=wave_capacity_soft_rule)

    def limit_wave_slack_rule(model, w):
        return model.maxWaveSlack[w] <= max_slack_limit

    model.LimitWaveSlack = Constraint(model.Waves, rule=limit_wave_slack_rule)

    # Solve
    solver = SolverFactory('glpk')
    result = solver.solve(model, tee=True)

    # Initialize the file path for results
    optimized_file_path = 'results/optimized_data.csv'

    # Update results in the spreadsheet
    if result.solver.status == SolverStatus.ok and result.solver.termination_condition == TerminationCondition.optimal:
        for p in model.Properties:
            for w in model.Waves:
                data.loc[data['Property'] == p, w] = int(model.Assign[p, w].value)
        data.to_csv(optimized_file_path, index=False)
        print(f"Optimization complete. Results saved to {optimized_file_path}")
        return optimized_file_path
    else:
        print("No optimal solution found.")
        return None

# Test the MIP solver with data file
mip_optimization_with_data('results/optimized_data.csv')
