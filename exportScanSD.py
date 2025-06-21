import os
import numpy as np
import struct
import re
import warnings
from typing import Tuple, List, Dict, Any, Optional, Union


def write_string(file_handle, s: str):
    """Writes a string in the *.scan format (length as double, chars as doubles)."""
    s_encoded = s.encode('ascii') # *.scan seems to use simple ASCII
    length = len(s_encoded)
    # Write length as a double
    file_handle.write(struct.pack('<d', float(length)))
    # Write each character's integer value as a double
    for char_int in s_encoded:
        file_handle.write(struct.pack('<d', float(char_int)))

def write_double(file_handle, value: Union[int, float]):
    """Writes a single double in little-endian format."""
    file_handle.write(struct.pack('<d', float(value)))

def write_double_array(file_handle, arr: np.ndarray):
    """Writes a numpy array of doubles in little-endian format."""
    # Ensure array is flat and of type float64 before writing
    arr_flat = arr.astype(np.float64).flatten()
    file_handle.write(arr_flat.tobytes(order='C')) # tobytes default is 'C' order if contiguous
                                                  # but flatten() returns C-contiguous, so this is fine.
                                                  # We manage Fortran order flattening later for data.


def export_scan(
    filename_out: str,
    coords: list,
    data: np.ndarray,
    freqs: np.ndarray,
    dim_size: np.ndarray,
    header: Union[List[Any], Tuple[Any, ...]],
):
    """
    Exports data to a ".scan" file format readable by import_scan.

    Args:
        filename_out: Path to the output file. If no extension, ".scan" is added.
        coords: Tuple or List of 1D numpy arrays for spatial coordinates.
                If is_uniform: Each array is unique coordinates for one dimension.
                If not is_uniform: Each array contains the coordinate for each point.
        freqs: 1D numpy array of frequencies (in GHz).
        data: Numpy array containing measurement data.
              If is_uniform: Shape (D1, D2, ..., Dn, Nf, Nc)
              If not is_uniform: Shape (Npoints, Nf, Nc)
        header_string: User, date, time info string.
        description_string: Scan description string.
        device_name_string: Measurement device name string.
        channel_names: List of strings for channel names.
        is_uniform: Flag indicating if the scan grid is uniform.

    Raises:
        ValueError: If input shapes, types, or consistency checks fail.
        IOError: If there's an error writing the file.
    """

    try:
        # Required keys - use direct access for KeyError if missing
        header_string = header[0]
        description_string = header[1]
        # Use .get() for flexible/alternative keys, but require one of them
        device_name_string = header[2]
        channel_names = header[3]
        # is_uniform flag is required and dictates data structure
        is_uniform = bool(header[4])
    except Exception as e:
        print("bad header formatting: " + str(e))

    if not isinstance(coords, list):
        raise ValueError("'coords' must be a list of arrays.")

    if len(coords) != 2:
         raise ValueError(f"'coords' must be a list of two sets, but got {len(coords)} sets.")

    coords_to_write = [coords[1], coords[0]]        #flip to match mathlab
    dim_size_to_write = np.flip(dim_size)
    num_spatial_points = int(np.prod(dim_size)) if is_uniform else dim_size[0]
    num_dims = len(coords) # dimensions (X, Y) based on the 2 columns

    if not isinstance(freqs, np.ndarray) or freqs.ndim != 1:
         raise ValueError("freqs must be a 1D numpy array.")
    num_f = len(freqs)

    if not isinstance(data, np.ndarray):
        raise ValueError("data must be a numpy array.")

    if data.ndim < 2: # Must have at least Frequency and Channel dimensions
         raise ValueError("data must have at least 2 dimensions (Npoints, Nf, Nc).")

    # Infer Nc from data shape (last dimension)
    num_channels_from_data = data.shape[-1]

    num_channels = len(channel_names)
    if num_channels != num_channels_from_data:
        raise ValueError(f"Number of channel names in header_info ({num_channels}) does not match the number of channels in the data array ({num_channels_from_data}).")


    # Validate non-uniform data shape against inferred points, Nf, Nc
    expected_data_shape = (num_spatial_points, num_f, num_channels)
    if data.shape != expected_data_shape:
         raise ValueError(f"For a (Npoints, 2) coords input (implying non-uniform 2D scan), input data shape {data.shape} must match (Npoints, Nf, Nc) = {expected_data_shape}, based on coords length ({num_spatial_points}), freqs length ({num_f}), and channel count ({num_channels}).")

    is_complex = np.iscomplexobj(data)

    # --- Prepare Data for Writing (Non-uniform logic only) ---
    # Input shape: (Npoints, Nf, Nc)
    # Target shape before flattening: (Nf, Nc, Npoints)
    # Transpose axes: (1, 2, 0)
    transpose_axes = (1, 2, 0)
    try:
        data_reshaped_for_flatten = np.transpose(data, axes=transpose_axes)
        # Shape is now already (Nf, Nc, Nspatial=Npoints)
    except ValueError as e:
        raise ValueError(f"Error preparing non-uniform data for writing. Input shape {data.shape}, transpose axes {transpose_axes}. Error: {e}")

    # Flatten the data in Fortran order
    data_flat_fortran = data_reshaped_for_flatten.flatten('F')

    # Separate complex data into real and imaginary parts if needed
    if is_complex:
        data_real_flat = data_flat_fortran.real
        data_imag_flat = data_flat_fortran.imag
        # Combine real and imaginary parts as [R1..RN, I1..IN]
        data_to_write = np.concatenate((data_real_flat, data_imag_flat))
    else:
        data_to_write = data_flat_fortran


    # --- Open File and Write Data ---
    script_dir = os.path.dirname(__file__)
    scan_dir = os.path.join(script_dir, 'scans')
    os.makedirs(scan_dir, exist_ok=True)

    name_part, ext = os.path.splitext(filename_out)
    if not ext:
        filename = os.path.join(scan_dir, name_part + ".scan")
    else:
        filename = os.path.join(scan_dir, filename_out)

    try:
        with open(filename, 'wb') as f:
            # 1. Write fixed header
            write_double(f, 63474328.0) # scan_file_code
            write_double(f, 1.0)        # scan_file_version

            # 2. Write string fields (using the extracted values)
            write_string(f, header_string)
            write_string(f, description_string)
            write_string(f, device_name_string)

            # 3. Write uniform flag (Must be False for this coords format)
            write_double(f, is_uniform) # This will be 1.0

            # 4. Write dimension info
            write_double(f, num_dims) # This will be 2

            # dim_order: hard coded for 2D scans (Y, X) to match matlab
            dim_order_to_write = np.array((1, 0))
            write_double_array(f, dim_order_to_write)

            # dim_size: sizes of dimensions (inferred from coords/data)
            write_double_array(f, dim_size)


            # 5. Write channel info
            write_double(f, num_channels)
            for name in channel_names:
                write_string(f, name)

            # 6. Write frequency info
            write_double(f, num_f)
            write_double(f, is_complex)

            # 7. Write Coordinate Data (Non-uniform logic only)
            for c in coords:
                write_double_array(f, c)
            # 7.5 duplicate for what would be absolute coordinates (we're using absolute coords in coords)
            for c in coords_to_write:
                write_double_array(f, c)

            # 8. Write frequency vector
            write_double_array(f, freqs)

            # 9. Write Measurement Data
            write_double_array(f, data_to_write)

    except Exception as e:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                warnings.warn(f"Failed to remove incomplete file: {filename}", UserWarning)
        raise IOError(f"Error writing scan file '{filename}': {e}") from e