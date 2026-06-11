"""Tests for sparkline integration in concept03 KPI viewmodel."""

from datetime import datetime, timezone


from app.services.status_service import StatusService
from app.services.trend_service import TrendService
from app.simulation.equations import calculate_operating_point
from app.simulation.parameters import ControlMode, SimulationParameters
from app.simulation.state import (
    OperationStatus,
    SimulationHistory,
    SimulationResult,
    SimulationState,
    TrendPoint,
)
from app.ui.viewmodels.concept03_kpi import build_concept03_kpi_view


def _build_test_result() -> SimulationResult:
    """Build a test simulation result."""
    parameters = SimulationParameters()
    operating_point = calculate_operating_point(parameters, step_minutes=0)

    # Convert OperatingPoint to SimulationState
    state = SimulationState(
        timestamp=datetime.now(timezone.utc),
        control_mode=ControlMode.AUTO,
        actual_airflow_m3_h=operating_point.actual_airflow_m3_h,
        demanded_airflow_m3_h=operating_point.demanded_airflow_m3_h,
        mixed_air_temp_c=operating_point.mixed_air_temp_c,
        recovered_air_temp_c=operating_point.recovered_air_temp_c,
        supply_temp_c=operating_point.supply_temp_c,
        room_temp_c=operating_point.room_temp_c,
        heating_power_kw=operating_point.heating_power_kw,
        heater_load_ratio=operating_point.heater_load_ratio,
        fan_power_kw=operating_point.fan_power_kw,
        total_power_kw=operating_point.total_power_kw,
        energy_intensity_kw_per_1000_m3_h=operating_point.energy_intensity_kw_per_1000_m3_h,
        filter_pressure_drop_pa=operating_point.filter_pressure_drop_pa,
        heat_balance_kw=operating_point.heat_balance_kw,
        status=OperationStatus.NORMAL,
    )

    # Generate trend
    trend_service = TrendService()
    trend = trend_service.generate(parameters)

    return SimulationResult(
        timestamp=datetime.now(timezone.utc),
        parameters=parameters,
        state=state,
        trend=trend,
    )


def test_kpi_view_without_history():
    """Test KPI view builds correctly without history (no sparklines)."""
    result = _build_test_result()
    view = build_concept03_kpi_view(result, history=None)

    assert view is not None
    assert len(view.rows) == 6
    # All sparkline_values should be None when no history provided
    for row in view.rows:
        assert row.sparkline_values is None


def test_kpi_view_with_empty_history():
    """Test KPI view with empty history."""
    result = _build_test_result()
    history = SimulationHistory(step_minutes=5, elapsed_minutes=0, points=[])
    view = build_concept03_kpi_view(result, history=history)

    assert view is not None
    # All sparkline_values should be empty tuples
    for row in view.rows:
        if row.sparkline_values is not None:
            assert len(row.sparkline_values) == 0


def test_kpi_view_with_history():
    """Test KPI view with history data generates sparklines."""
    result = _build_test_result()

    # Create history with 10 points
    points = [
        TrendPoint(
            minute=i * 5,
            outdoor_temp_c=-10.0 + i * 0.5,
            supply_temp_c=20.0 + i * 0.2,
            room_temp_c=22.0 + i * 0.1,
            heating_power_kw=5.0 + i * 0.3,
            total_power_kw=6.0 + i * 0.4,
            airflow_m3_h=1000.0 + i * 10,
            demanded_airflow_m3_h=1000.0,
            filter_pressure_drop_pa=100.0 + i * 5,
        )
        for i in range(10)
    ]
    history = SimulationHistory(step_minutes=5, elapsed_minutes=45, points=points)

    view = build_concept03_kpi_view(result, history=history)

    assert view is not None

    # Check that sparkline data is present for relevant KPIs
    airflow_row = next(r for r in view.rows if r.kpi_id == "kpi-row-airflow")
    assert airflow_row.sparkline_values is not None
    assert len(airflow_row.sparkline_values) == 10
    assert airflow_row.sparkline_values[0] == 1000.0
    assert airflow_row.sparkline_values[-1] == 1090.0

    pressure_row = next(r for r in view.rows if r.kpi_id == "kpi-row-pressure")
    assert pressure_row.sparkline_values is not None
    assert len(pressure_row.sparkline_values) == 10
    assert pressure_row.sparkline_values[0] == 100.0
    assert pressure_row.sparkline_values[-1] == 145.0

    supply_temp_row = next(r for r in view.rows if r.kpi_id == "kpi-row-supply-temp")
    assert supply_temp_row.sparkline_values is not None
    assert len(supply_temp_row.sparkline_values) == 10

    power_row = next(r for r in view.rows if r.kpi_id == "kpi-row-power")
    assert power_row.sparkline_values is not None
    assert len(power_row.sparkline_values) == 10


def test_kpi_view_limits_sparkline_points():
    """Test that sparkline data is limited to last 12 points."""
    result = _build_test_result()

    # Create history with 20 points (more than the 12-point limit)
    points = [
        TrendPoint(
            minute=i * 5,
            outdoor_temp_c=-10.0,
            supply_temp_c=20.0,
            room_temp_c=22.0,
            heating_power_kw=5.0,
            total_power_kw=6.0,
            airflow_m3_h=1000.0 + i * 10,
            demanded_airflow_m3_h=1000.0,
            filter_pressure_drop_pa=100.0,
        )
        for i in range(20)
    ]
    history = SimulationHistory(step_minutes=5, elapsed_minutes=95, points=points)

    view = build_concept03_kpi_view(result, history=history)

    airflow_row = next(r for r in view.rows if r.kpi_id == "kpi-row-airflow")
    assert airflow_row.sparkline_values is not None
    # Should be limited to 12 points
    assert len(airflow_row.sparkline_values) == 12
    # Should be the last 12 points (indices 8-19)
    assert airflow_row.sparkline_values[0] == 1080.0  # point 8
    assert airflow_row.sparkline_values[-1] == 1190.0  # point 19


def test_kpi_view_with_status_service():
    """Test KPI view with custom status service."""
    result = _build_test_result()
    status_service = StatusService()

    points = [
        TrendPoint(
            minute=i * 5,
            outdoor_temp_c=-10.0,
            supply_temp_c=20.0,
            room_temp_c=22.0,
            heating_power_kw=5.0,
            total_power_kw=6.0,
            airflow_m3_h=1000.0,
            demanded_airflow_m3_h=1000.0,
            filter_pressure_drop_pa=100.0,
        )
        for i in range(5)
    ]
    history = SimulationHistory(step_minutes=5, elapsed_minutes=20, points=points)

    view = build_concept03_kpi_view(result, status_service, history=history)

    assert view is not None
    assert len(view.rows) == 6

    # Verify sparklines are present
    for row in view.rows:
        if row.kpi_id in ["kpi-row-airflow", "kpi-row-pressure", "kpi-row-supply-temp", "kpi-row-power"]:
            assert row.sparkline_values is not None
            assert len(row.sparkline_values) == 5


def test_kpi_row_has_sparkline_field():
    """Test that KPI row dataclass has sparkline_values field."""
    result = _build_test_result()
    view = build_concept03_kpi_view(result)

    for row in view.rows:
        # Check that sparkline_values attribute exists
        assert hasattr(row, "sparkline_values")
        # Should be None when no history provided
        assert row.sparkline_values is None
