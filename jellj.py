import matplotlib.pyplot as plt
import numpy as np
from scipy.special import erf

# Define y_D range
y_D_values = np.linspace(0, 1, 100)

# Define the dimensionless times for which we want to plot the profile
t_D_values = [0.1, 0.2, 0.5, 1, 2]

# Create plot
plt.figure(figsize=(10, 6))

# Plot the dimensionless temperature profiles for specified t_D values
for i, t_D in enumerate(t_D_values):
    # Initialize the dimensionless temperature profile to y_D (steady-state part)
    theta = y_D_values.copy()

    # Approximate the transient part by summing the first 50 terms of the series
    for n in range(1, 51):
        theta += (2 / (n * np.pi)) * np.sin(n * np.pi * y_D_values) * np.exp(-(n * np.pi)**2 * t_D)

    plt.plot(y_D_values, theta, label=f"t_D = {t_D}")

    # Plot the new theta function only for t_D values of 0.1 and 0.2
    if t_D in [0.1, 0.2]:
        theta_new = erf(y_D_values / (2 * np.sqrt(t_D)))
        plt.plot(y_D_values, theta_new, '--', label=f"erf, t_D = {t_D}")

# Add labels and title
plt.xlabel("yd")
plt.ylabel("theta(yd, td)")
plt.title("Theta vs. yd for different values of td")

# Add legend
plt.legend()

# Show the plot
plt.grid(True)
plt.show()
