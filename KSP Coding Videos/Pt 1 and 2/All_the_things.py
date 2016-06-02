import krpc
import math
from numba import jit

conn = krpc.connect(name='name')

KSC = conn.space_center
vessel = KSC.active_vessel
ap = vessel.auto_pilot
control = vessel.control
parts = vessel.parts
engines = parts.with_module("ModuleEnginesRF")

body = vessel.orbit.body
bdy_reference_frame = conn.add_stream(getattr, body, 'reference_frame')
vessel_flight_bdy = conn.add_stream(vessel.flight, bdy_reference_frame())
vessel_speed = conn.add_stream(getattr, vessel_flight_bdy(), 'speed')

ETA_ap = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')


def twr():
    _thrust = vessel.thrust
    _mu = vessel.orbit.body.gravitational_parameter
    _Radius_eq = vessel.orbit.body.equatorial_radius
    _mass = vessel.mass
    _alt = vessel.flight().mean_altitude

    _twr = (_thrust / ((_mu / ((_alt + _Radius_eq) ** 2)) * _mass))
    return _twr


@jit(nopython=True)
def pitch(_speed):
    _pitch = (90 - (1.4 * math.sqrt(_speed)))
    return _pitch


def eng_status(spin_solids):
    for _en in engines:
        if _en.engine.active and (_en.name != spin_solids):
            _mod = _en.modules
            for _m in _mod:
                if _m.name == "ModuleEnginesRF":
                    return _m.get_field("Status")


def get_active_engine_list():
    _active_engines_list = []
    for _eng in engines:
        if _eng.engine.active:
            _active_engines_list.append(_eng)
    return _active_engines_list


def get_active_engine():
    for _eng in engines:
        if _eng.engine.active:
            return _eng


def stage_deltav():
    _engine = get_active_engine()
    _prop_used = _engine.engine.propellants
    _stage = _engine.decouple_stage
    _parts = vessel.parts.in_decouple_stage(_stage)
    _total_fuel_mass = 0
    for _p in _parts:
        if _p.resources.names == _prop_used:
            _dry_mass = _p.dry_mass
            _wet_mass = _p.mass
            _total_fuel_mass = _total_fuel_mass + (_wet_mass - _dry_mass)

    _ve = _engine.engine.specific_impulse * 9.8
    _delta_v = _ve * math.log(vessel.mass / (vessel.mass - _total_fuel_mass))
    return _delta_v
