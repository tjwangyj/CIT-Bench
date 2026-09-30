"""State shared by the benchmark loader and graphics view."""
class ProjectModel:
    def __init__(self):
        self.case_name = ''
        self.source_directory = None
        self.floorplan = {}
        self.netlist = {'nets': []}
        self.power_report = None
        self.chiplet_sizes = {}
        self.chiplet_global_pos = {}
        self.bumps = {}
        self.chip_conflicts = set()

    def clear_layout_data(self):
        self.chiplet_sizes.clear()
        self.chiplet_global_pos.clear()
        self.bumps.clear()
        self.chip_conflicts.clear()
