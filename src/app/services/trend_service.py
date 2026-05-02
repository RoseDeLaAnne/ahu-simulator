from app.simulation.equations import calculate_operating_point
from app.simulation.parameters import SimulationParameters
from app.simulation.state import TrendPoint, TrendSeries


class TrendService:
    def generate(self, parameters: SimulationParameters) -> TrendSeries:
        points = [
            self._build_point(
                minute=0,
                parameters=parameters,
                operating_point=calculate_operating_point(parameters, step_minutes=0),
            )
        ]

        rolling_parameters = parameters.model_copy(deep=True)
        for minute in range(
            parameters.step_minutes,
            parameters.horizon_minutes + parameters.step_minutes,
            parameters.step_minutes,
        ):
            operating_point = calculate_operating_point(
                rolling_parameters,
                step_minutes=parameters.step_minutes,
            )
            rolling_parameters = rolling_parameters.model_copy(
                update={"room_temp_c": operating_point.room_temp_c}
            )
            points.append(
                self._build_point(
                    minute=minute,
                    parameters=rolling_parameters,
                    operating_point=operating_point,
                )
            )

        return TrendSeries(
            horizon_minutes=parameters.horizon_minutes,
            step_minutes=parameters.step_minutes,
            points=points,
        )

    @staticmethod
    def _build_point(
        minute: int,
        parameters: SimulationParameters,
        operating_point,
    ) -> TrendPoint:
        return TrendPoint(
            minute=minute,
            outdoor_temp_c=parameters.outdoor_temp_c,
            supply_temp_c=operating_point.supply_temp_c,
            room_temp_c=operating_point.room_temp_c,
            heating_power_kw=operating_point.heating_power_kw,
            total_power_kw=operating_point.total_power_kw,
            airflow_m3_h=operating_point.actual_airflow_m3_h,
            filter_pressure_drop_pa=operating_point.filter_pressure_drop_pa,
        )
