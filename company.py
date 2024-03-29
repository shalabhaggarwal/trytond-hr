# -*- coding: utf-8 -*-
"""
    Company

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, Workflow, fields
from dateutil.relativedelta import relativedelta
from datetime import datetime

from trytond.pyson import Eval, Bool
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = [
    'Department', 'Employee', 'Responsibility', 'Language', 'Academic',
    'Skill', 'Team', 'TransferProposal', 'TransferRemark', 'Party',
    'PaymentDetail', 'EmployeeHistory',
]

STATES = {
    'readonly': ~Eval('active', True),
}

__metaclass__ = PoolMeta


class Department(ModelView, ModelSQL):
    "Company Department"
    __name__ = 'company.department'

    name = fields.Char('Name', required=True, states=STATES)
    active = fields.Boolean('Active')
    company = fields.Many2One(
        'company.company', 'Company', required=True, states=STATES,
    )
    parent = fields.Many2One(
        'company.department', 'Parent',
        domain=[
            ('company', '=', Eval('company')),
            ('id', '!=', Eval('id'))
        ],
        depends=['company', 'id'], states=STATES,
    )
    # Attendance specific config
    early_departure_time = fields.Time('Early Departure Time', states=STATES)
    allowed_early_departures = fields.Integer(
        'Allowed Early Departures (per month)', states=STATES
    )
    late_coming_time = fields.Time('Late Coming Time', states=STATES)
    allowed_late_comings = fields.Integer(
        'Allowed Late Comings (per month)', states=STATES
    )

    @staticmethod
    def default_allowed_early_departures():
        return 2

    @staticmethod
    def default_allowed_late_comings():
        return 2

    @staticmethod
    def default_active():
        return True


class Party:
    "Party"
    __name__ = 'party.party'
    _history = True


class Employee:
    "Employee"
    __name__ = "company.employee"
    _history = True

    department = fields.Many2One(
        'company.department', 'Department', required=True,
        domain=[('company', '=', Eval('company'))]
    )
    photo = fields.Binary('Photo')
    state = fields.Selection([
            ('current', 'Current'),
            ('retired', 'Retired'),
            ('closed', 'Closed'),
        ], 'State', required=True,
    )
    first_name = fields.Char('First Name', required=True)
    middle_name = fields.Char('Middle Name')
    last_name = fields.Char('Last Name', required=True)
    employee_id = fields.Char('Employee ID', readonly=True)
    manager = fields.Many2One(
        'company.employee', 'Manager',
        domain=[('id', '!=', Eval('id'))],
        depends=['id'],
    )
    permanent_address = fields.Many2One(
        'party.address', 'Permanent Address', required=True,
        domain=[('party', '=', Eval('party'))],
        depends=['party'],
    )
    present_address = fields.Many2One(
        'party.address', 'Present Address', required=True,
        domain=[('party', '=', Eval('party'))],
        depends=['party'],
    )
    addresses = fields.Function(
        fields.One2Many('party.address', 'party', 'Addresses'),
        'get_addresses', 'set_addresses'
    )
    contact_mechanisms = fields.Function(
        fields.One2Many('party.contact_mechanism', 'party', 'Contact Mechanisms'),
        'get_contact_mechanisms', 'set_contact_mechanisms'
    )
    sex = fields.Selection([
            ('male', 'Male'),
            ('female', 'Female')
        ], 'Sex', required=True
    )
    date_of_birth = fields.Date('Date of Birth', required=True)

    # TODO: Not implemented for death
    age = fields.Function(
        fields.Char('Age', on_change_with=['date_of_birth']),
        'get_age'
    )
    place_of_birth = fields.Char('Place of Birth', required=True)
    marital_status = fields.Selection([
            ('single', 'Single'),
            ('married', 'Married')
        ], 'Marital Status', required=True
    )
    wedding_date = fields.Date(
        'Wedding Date',
        states={
            'invisible': Eval('marital_status') == 'single',
            'required': Eval('marital_status') == 'married'
        },
    )
    marriage_license = fields.Char(
        'Marriage License',
        states={
            'invisible': Eval('marital_status') == 'single',
            'required': Eval('marital_status') == 'married'
        },
    )
    nationality = fields.Many2One(
        'country.country', 'Nationality', required=True,
    )
    native_state = fields.Many2One(
        'country.subdivision', 'Native State',
        domain=[('country', '=', Eval('nationality'))],
        depends=['nationality'],
    )
    language_skills = fields.One2Many(
        'company.employee.language', 'employee', 'Language Skills'
    )
    religion = fields.Char('Religion') #TODO: many2one to employee.religion
    denomination = fields.Char('Denomination') #TODO: m2o to employee.denomination
    driving_license = fields.Char('Driving License')
    driving_license_validity = fields.Date(
        'Driving License Validity',
        states={'required': Bool(Eval('driving_license'))},
    )
    passport_number = fields.Char('Passport Number')
    passport_validity = fields.Date(
        'Passport Validity',
        states={'required': Bool(Eval('passport_number'))},
    )
    academics = fields.One2Many(
        'company.employee.academic', 'employee', 'Academics'
    )
    skills = fields.One2Many(
        'company.employee.skill', 'employee', 'Skills'
    )
    responsibilities = fields.One2Many(
        'company.employee.responsibility', 'employee', 'Responsibilities'
    )
    team = fields.One2Many(
        'company.employee.team', 'employee', 'Team'
    )
    transfers = fields.One2Many(
        'employee.transfer.proposal', 'employee',
        'Promotion / Transfer Proposals'
    )
    payment_details = fields.One2Many(
        'company.employee.payment_detail', 'employee', 'Payment Details'
    )
    history = fields.One2Many('company.employee.history', 'employee',
        'History', readonly=True
    )
    attendance = fields.One2Many(
        'employee.attendance', 'employee', 'Attendance'
    )
    type = fields.Selection([
        ('probation', 'Probation'),
        ('confirmed', 'Confirmed')
    ], 'Type', required=True)

    current_payrollyear = fields.Function(
        fields.Many2One('payroll.year', 'Current Payroll Year'),
        'get_current_payrollyear'
    )
    leave_applications = fields.One2Many(
        'employee.leave.application', 'employee', 'Leave Applications'
    )
    available_cl = fields.Function(
        fields.Integer('Available Casual Leaves'), 'get_available_cl'
    )
    available_sl = fields.Function(
        fields.Integer('Available Sick Leaves'), 'get_available_sl'
    )
    available_el = fields.Function(
        fields.Integer('Available Earned Leaves'), 'get_available_el'
    )
    available_dl = fields.Function(
        fields.Integer('Available Study Leaves'), 'get_available_dl'
    )
    available_pl = fields.Function(
        fields.Integer('Available Paternity Leaves'), 'get_available_pl'
    )
    available_al = fields.Function(
        fields.Integer('Available Annual Leaves'), 'get_available_al'
    )

    @classmethod
    def __setup__(cls):
        super(Employee, cls).__setup__()
        cls._error_messages.update({
            'payrollyear_not_found': \
                'Payroll Year not found for today!',
        })

    @staticmethod
    def default_type():
        return 'confirmed'

    @staticmethod
    def default_state():
        return 'current'

    @staticmethod
    def default_sex():
        return 'male'

    @staticmethod
    def default_marital_status():
        return 'single'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def create(cls, values):
        Sequence = Pool().get('ir.sequence')
        Configuration = Pool().get('company.employee.configuration')

        values = values.copy()
        config = Configuration(1)
        values['employee_id'] = Sequence.get_id(config.employee_sequence.id)
        return super(Employee, cls).create(values)

    def get_current_payrollyear(self, name):
        PayrollYear = Pool().get('payroll.year')
        Date = Pool().get('ir.date')

        date = Date.today()
        years = PayrollYear.search([
            ('state', '=', 'open'),
            ('start_date', '<=', date),
            ('end_date', '>=', date),
        ])
        if not years or len(years) > 1:
            self.raise_user_error('payrollyear_not_found')

        return years[0].id

    def get_addresses(self, name):
        """
        Return all the addresses of the party as the address of the employee
        """
        return map(int, self.party.addresses)

    def calculate_leaves(self, type):
        """Calculate leaves as per given type

        :param type: Type for which leaves have to be calculated
        """
        leaves = 0
        for attendance in self.attendance:
            if attendance.date >= self.current_payrollyear.start_date \
                    and attendance.date <= self.current_payrollyear.end_date:
                if attendance.on_leave and \
                        attendance.leave_application.leave_type == type:
                    leaves += 1

        return leaves

    def get_available_cl(self, name):
        "Calculate remaining casual leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        cl_taken = self.calculate_leaves('casual')
        if self.type == 'probation':
            allowed_cl = config.probation_cl or 0
        else:
            allowed_cl = config.confirmed_cl or 0

        return allowed_cl - cl_taken

    def get_available_sl(self, name):
        "Calculate remaining sick leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        sl_taken = self.calculate_leaves('sick')
        if self.type == 'probation':
            allowed_sl = config.probation_sl or 0
        else:
            allowed_sl = config.confirmed_sl or 0

        return allowed_sl - sl_taken

    def get_available_el(self, name):
        "Calculate remaining earned leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        el_taken = self.calculate_leaves('earned')
        if self.type == 'probation':
            allowed_el = config.probation_el or 0
        else:
            allowed_el = config.confirmed_el or 0

        return allowed_el - el_taken

    def get_available_dl(self, name):
        "Calculate remaining study leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        dl_taken = self.calculate_leaves('study')
        if self.type == 'probation':
            allowed_dl = config.probation_dl or 0
        else:
            allowed_dl = config.confirmed_dl or 0

        return allowed_dl - dl_taken

    def get_available_pl(self, name):
        "Calculate remaining paternity leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        pl_taken = self.calculate_leaves('paternity')
        if self.type == 'probation':
            allowed_pl = config.probation_pl or 0
        else:
            allowed_pl = config.confirmed_pl or 0

        return allowed_pl - pl_taken

    def get_available_al(self, name):
        "Calculate remaining annual leaves in current payroll year"
        LeaveConfig = Pool().get('employee.leave.configuration')

        config = LeaveConfig(1)
        al_taken = self.calculate_leaves('annual')
        if self.type == 'probation':
            allowed_al = config.probation_al or 0
        else:
            allowed_al = config.confirmed_al or 0

        return allowed_al - al_taken

    @classmethod
    def set_addresses(cls, records, name, value=None):
        """
        Set the address as the address of the party
        """
        Party = Pool().get('party.party')

        for record in records:
            Party.write([record.party], {'addresses': value})

    def get_contact_mechanisms(self, name):
        """
        Return all the contact_mechanisms of the party as the
        contact_mechanism of the employee
        """
        return map(int, self.party.contact_mechanisms)

    @classmethod
    def set_contact_mechanisms(cls, records, name, value=None):
        """
        Set the contact_mechanism as the contact_mechanism of the party
        """
        Party = Pool().get('party.party')

        for record in records:
            Party.write([record.party], {'contact_mechanisms': value})

    def get_age(self, name=None):
        """
        Retrun age of employee
        """
        now = datetime.now()
        delta = relativedelta(now, self.date_of_birth)
        years_months_days = str(delta.years) + 'y ' + str(delta.months) + \
                'm ' + str(delta.days) + 'd'
        return years_months_days

    def on_change_with_age(self):
        if self.date_of_birth:
            return self.get_age()


class EmployeeHistory(ModelSQL, ModelView):
    "Employee History"
    __name__ = 'company.employee.history'
    _rec_name = 'employee'

    employee = fields.Many2One('company.employee', 'Employee')
    date = fields.DateTime('Change Date')
    user = fields.Many2One('res.user', 'User')
    party = fields.Many2One('party.party', 'Party', datetime_field='date')
    company = fields.Many2One(
        'company.company', 'Company', datetime_field='date'
    )
    photo = fields.Binary('Photo')
    state = fields.Selection([
            ('current', 'Current'),
            ('retired', 'Retired'),
            ('closed', 'Closed'),
        ], 'State'
    )
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    last_name = fields.Char('Last Name')
    employee_id = fields.Char('Employee ID')
    manager = fields.Many2One(
        'company.employee', 'Manager', datetime_field='date'
    )
    permanent_address = fields.Many2One(
        'party.address', 'Permanent Address', datetime_field='date',
    )
    present_address = fields.Many2One(
        'party.address', 'Present Address', datetime_field='date',
    )
    sex = fields.Selection([
            ('male', 'Male'),
            ('female', 'Female')
        ], 'Sex'
    )
    date_of_birth = fields.Date('Date of Birth')
    place_of_birth = fields.Char('Place of Birth')
    marital_status = fields.Selection([
            ('single', 'Single'),
            ('married', 'Married')
        ], 'Marital Status'
    )
    wedding_date = fields.Date('Wedding Date')
    marriage_license = fields.Char('Marriage License')
    nationality = fields.Many2One(
        'country.country', 'Nationality', datetime_field='date',
    )
    native_state = fields.Many2One(
        'country.subdivision', 'Native State', datetime_field='date',
    )
    religion = fields.Char('Religion')
    #TODO: many2one to employee.religion
    denomination = fields.Char('Denomination')
    #TODO: m2o to employee.denomination
    driving_license = fields.Char('Driving License')
    driving_license_validity = fields.Date('Driving License Validity')
    passport_number = fields.Char('Passport Number')
    passport_validity = fields.Date('Passport Validity')

    @classmethod
    def __setup__(cls):
        super(EmployeeHistory, cls).__setup__()
        cls._order.insert(0, ('date', 'DESC'))

    @classmethod
    def _table_query_fields(cls):
        Employee = Pool().get('company.employee')
        table = '%s__history' % Employee._table
        return [
            'MIN("%s".__id) AS id' % table,
            '"%s".id AS employee' % table,
            ('MIN(COALESCE("%s".write_date, "%s".create_date)) AS date'
                % (table, table)),
            ('COALESCE("%s".write_uid, "%s".create_uid) AS user'
                % (table, table)),
            ] + ['"%s"."%s"' % (table, name)
                for name, field in cls._fields.iteritems()
                if name not in ('id', 'employee', 'date', 'user')
                and not hasattr(field, 'set')]

    @classmethod
    def _table_query_group(cls):
        Employee = Pool().get('company.employee')
        table = '%s__history' % Employee._table
        return [
            '"%s".id' % table,
            'COALESCE("%s".write_uid, "%s".create_uid)' % (table, table),
        ] + ['"%s"."%s"' % (table, name)
                for name, field in cls._fields.iteritems()
                if name not in ('id', 'employee', 'date', 'user')
                and not hasattr(field, 'set')]

    @classmethod
    def table_query(cls):
        Employee = Pool().get('company.employee')
        return (('SELECT ' + (', '.join(cls._table_query_fields()))
                + ' FROM "%s__history" GROUP BY '
                + (', '.join(cls._table_query_group())))
            % Employee._table, [])


class TransferProposal(Workflow, ModelSQL, ModelView):
    "Employee Promotion and Transfer Proposal"
    __name__ = 'employee.transfer.proposal'
    _rec_name = 'employee'

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True
    )
    proposed_company = fields.Many2One(
        'company.company', 'Proposed Company', required=True
    )
    proposed_department = fields.Many2One(
        'company.department', 'Proposed Department', domain=[
            ('company', '=', Eval('proposed_company')),
        ], required=True, depends=['proposed_company']
    )
    proposed_allowance = fields.Numeric('Proposed Allowance', required=True)
    proposed_doj = fields.Date('Proposed Date of Joining', required=True)
    remarks = fields.One2Many(
        'employee.transfer.remark', 'proposal', 'Remarks'
    )
    state = fields.Selection([
        ('Draft', 'Draft'),
        ('In Review', 'In Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ], 'State', readonly=True, required=True)

    @staticmethod
    def default_state():
        return 'Draft'

    @classmethod
    def __setup__(cls):
        super(TransferProposal, cls).__setup__()
        cls._transitions |= set((
            ('Draft', 'In Review'),
            ('In Review', 'Approved'),
            ('In Review', 'Rejected'),
        ))
        cls._buttons.update({
            'review': {
                'invisible': Eval('state') != 'Draft',
            },
            'approve': {
                'invisible': Eval('state') != 'In Review',
            },
            'reject': {
                'invisible': Eval('state') != 'In Review',
            }
        })

    @classmethod
    @ModelView.button
    @Workflow.transition('In Review')
    def review(cls, proposals):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('Approved')
    def approve(cls, proposals):
        Employee = Pool().get('company.employee')

        for proposal in proposals:
            Employee.write([proposal.employee], {
                'company': proposal.proposed_company.id,
                'department': proposal.proposed_department.id,
            })

    @classmethod
    @ModelView.button
    @Workflow.transition('Rejected')
    def reject(cls, proposals):
        pass


class TransferRemark(ModelSQL, ModelView):
    "Employe Transfer Remark"
    __name__ = 'employee.transfer.remark'
    _rec_name = 'proposal'

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True
    )
    proposal = fields.Many2One(
        'employee.transfer.proposal', 'Proposal', required=True
    )
    date = fields.Date('Date', required=True)
    comment = fields.Text('Comment')
    remark = fields.Selection([
        ('recommended', 'Recommended'),
        ('not_recommended', 'Not Recommended'),
        ('average', 'Average'),
        ('rejected', 'Rejected')
    ], 'Remark', required=True)

    @staticmethod
    def default_remark():
        return 'recommended'

    @staticmethod
    def default_date():
        Date = Pool().get('ir.date')
        return Date.today()


class Responsibility(ModelSQL, ModelView):
    "Responsibility"
    __name__ = "company.employee.responsibility"

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True,
    )
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')


class Team(ModelSQL, ModelView):
    "Team"
    __name__ = "company.employee.team"

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True,
    )
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')


class Language(ModelSQL, ModelView):
    "Language"
    __name__ = "company.employee.language"

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True,
    )
    language = fields.Many2One(
        'ir.lang', 'Language', required=True,
    )
    mother_tounge = fields.Boolean('Mother Tounge')
    read = fields.Boolean('Read')
    write = fields.Boolean('Write')
    speak = fields.Boolean('Speak')

    @classmethod
    def __setup__(cls):
        super(Language, cls).__setup__()
        cls._sql_constraints = [
            ('employee_language_uniq', 'UNIQUE(employee, language)',
             'Employee should have unique language')
        ]
        # TODO: The should only be one mother tounge


class Skill(ModelSQL, ModelView):
    "Skill"
    __name__ = "company.employee.skill"

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True,
    )
    name = fields.Char('Name', required=True)


class Academic(ModelSQL, ModelView):
    "Academic"
    __name__ = "company.employee.academic"

    employee = fields.Many2One(
        'company.employee', 'Employee', required=True,
    )
    institution = fields.Char('Institution', required=True)
    major = fields.Char('Major', required=True)
    level = fields.Char('Level')
    year = fields.Integer('Year', required=True)
    percentage = fields.Numeric('Percentage', digits=(2, 2), required=True)



class PaymentDetail(ModelSQL, ModelView):
    "Payment Detail"
    __name__ = 'company.employee.payment_detail'

    employee = fields.Many2One('company.employee', 'Employee', required=True)
    active = fields.Boolean('Active')
    payment_mode = fields.Selection([
            ('cash', 'Cash'),
            ('cheque', 'Cheque'),
            ('bank', 'Bank'),
        ], 'Payment Mode',
    )
    payment_date = fields.Date('Payment Date')
    bank_code = fields.Char('Bank Code')
    bank_branch_code = fields.Char('Bank Branch Code')
    bank_account_name = fields.Char('Bank Account Name')
    payable_at_name = fields.Char('Payable at Name')
    return_date = fields.Date('Return Date')
    return_reason = fields.Char('Return Reason')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_payment_mode():
        return 'cash'
