import datetime

class WorkflowpyTime:
    in_fmt = '%Y-%m-%d_%H:%M:%S'
    out_fmt = '%Y%m%d%H%M%S'
    def __init__(self, time):
        wrf_h_start = datetime.datetime.strptime(time['start_wrf-h_time'],
                                                WorkflowpyTime.in_fmt)
        self.start = datetime.datetime.strptime(time['start_jedi_time'],
                                                WorkflowpyTime.in_fmt)
        self.end = datetime.datetime.strptime(time['end_time'],
                                              WorkflowpyTime.in_fmt)
        if wrf_h_start == self.start:
            self.pre_wrf_h = False
        else:
            self.pre_wrf_h = True
            self.save_start = self.start
            self.save_end = self.end
            self.end = self.start
            self.start = wrf_h_start
            self.pre_wrf_h_dt = self.end - self.start

        self.assim_window_hr = time['assim_window']['hours']
        self.dt = datetime.timedelta(hours=time['advance_model_hours'])
        self.prev = self.start - self.dt
        self.current = self.start
        self.future = self.start + self.dt
        self.stringify()
    def advance(self):
        self.prev += self.dt
        self.current += self.dt
        self.future += self.dt
        self.stringify()
    def stringify(self):
        self.prev_s = self.prev.strftime(WorkflowpyTime.out_fmt)
        self.current_s = self.current.strftime(WorkflowpyTime.out_fmt)
        self.future_s = self.future.strftime(WorkflowpyTime.out_fmt)
    def pre_wrf_h_done(self):
        self.start = self.save_start
        self.end = self.save_end
        self.prev = self.start - self.dt
        self.current = self.start
        self.future = self.start + self.dt
        self.stringify()
