import numpy as np
import struct
import os
import warnings
from typing import List, Dict, Any, Optional
import tkinter as tk
from tkinter import filedialog

def _write_string_as_doubles(file_handle, text_string: str):
    """Helper to write string length then each char as a double (ASCII value)."""
    file_handle.write(struct.pack('<d', float(len(text_string))))
    for char_val in text_string:
        file_handle.write(struct.pack('<d', float(ord(char_val))))

def export_scan(
    axis_coordinates: List[np.ndarray],
    f_vector: np.ndarray,
    data: np.ndarray,
    header_in: Optional[Dict[str, Any]] = None,
    is_uniform: bool = True,
    filename_in: Optional[str] = None
):
    """
    Exports data to a ".scan" file format, similar to amntl scanner program.

    Args:
        axis_coordinates: List of 1D NumPy arrays for each spatial dimension's coordinates.
                          For uniform data, numel(axis_coordinates[i]) == data.shape[i].
                          For non-uniform, len(axis_coordinates[i]) == data.shape[0].
        f_vector: 1D NumPy array of frequencies (e.g., in GHz).
        data: NumPy array of measurement data.
              If uniform: shape is (S0, S1, ..., S(n-1), Nf, Nc) or (S0, ..., S(n-1), Nf) if Nc=1.
                          Si is size of axis_coordinates[i].
              If non-uniform: shape is (NumPoints, Nf, Nc) or (NumPoints, Nf) if Nc=1.
        header_in: Optional dictionary for header fields:
                   'header': str (user, date, time info).
                   'description': str (scan description).
                   'device_name': str (measurement device name).
                   'channel_names': List[str] (channel names).
        is_uniform: Boolean, True if scan grid is uniform, False otherwise. Defaults to True.
        filename_in: Optional path to the output file. If None, a save dialog is shown.
                     If path has no extension, ".scan" will be automatically appended.
    Raises:
        ValueError: For inconsistent input sizes or issues writing the file.
        TypeError: For incorrect argument types.
    """

    # --- Argument Type Basic Validation ---
    if not isinstance(axis_coordinates, list) or \
       not all(isinstance(arr, np.ndarray) and arr.ndim == 1 for arr in axis_coordinates):
        raise TypeError("axis_coordinates must be a list of 1D NumPy arrays.")
    if not isinstance(f_vector, np.ndarray) or f_vector.ndim != 1:
        raise TypeError("f_vector must be a 1D NumPy array.")
    if not isinstance(data, np.ndarray):
        raise TypeError("data must be a NumPy array.")
    if header_in is not None and not isinstance(header_in, dict):
        raise TypeError("header_in must be a dictionary or None.")
    if not isinstance(is_uniform, bool):
        raise TypeError("is_uniform must be a boolean.")

    # --- Check Input Sizes and Determine Derived Parameters ---
    num_dims = len(axis_coordinates)
    dim_size_np = np.array([coord_vec.size for coord_vec in axis_coordinates], dtype=int)
    data_shape = np.array(data.shape) # So we can index it like MATLAB

    num_dims_for_file = num_dims # May be adjusted for non-uniform 0D spatial scans

    if is_uniform:
        if num_dims > 0:
            if not np.array_equal(dim_size_np, data_shape[:num_dims]):
                raise ValueError(
                    f"Inconsistent dimension sizes for uniform data. "
                    f"First {num_dims} dimensions of Data {data_shape[:num_dims]} "
                    f"do not match lengths of axis_coordinates {dim_size_np}.")
        
        # Expected data.ndim: num_dims + 1 (for Nf) or num_dims + 2 (for Nf, Nc)
        min_expected_ndim = num_dims + 1
        max_expected_ndim = num_dims + 2
        if not (min_expected_ndim <= data.ndim <= max_expected_ndim):
            raise ValueError(
                f"Uniform Data has {data.ndim} dimensions. Expected {min_expected_ndim} (if Nc=1 implicit) "
                f"or {max_expected_ndim} (if Nc explicit). Spatial dims: {num_dims}.")

        nf_dim_index = num_dims
        if f_vector.size != data_shape[nf_dim_index]:
            raise ValueError(
                f"Inconsistent frequency dimension for uniform data. "
                f"Data dimension {nf_dim_index} (size {data_shape[nf_dim_index]}) "
                f"does not match length of f_vector ({f_vector.size}).")
        
        num_channels = data_shape[num_dims + 1] if data.ndim == (num_dims + 2) else 1
        file_dim_size_param = dim_size_np # dimSize written to file
    else: # Non-uniform
        if num_dims > 0:
            for i, coord_vec_len in enumerate(dim_size_np):
                if coord_vec_len != data_shape[0]: # NumPoints
                    raise ValueError(
                        f"Inconsistent points dimension for non-uniform data. "
                        f"Length of axis_coordinates[{i}] ({coord_vec_len}) does not match "
                        f"Data's first dimension (NumPoints = {data_shape[0]}).")
        elif data.ndim == 0 : # Data is a scalar, non-uniform. This is ill-defined.
             raise ValueError("Non-uniform scalar data is not supported. Must have at least NumPoints dimension.")


        # Expected data.ndim: 1 (NumPoints, if Nf=1, Nc=1 implicit), 2 (NumPoints, Nf), or 3 (NumPoints, Nf, Nc)
        # The MATLAB script expects at least 2D (Npts, Nf).
        min_expected_ndim = 2 # NumPoints, Nf
        max_expected_ndim = 3 # NumPoints, Nf, Nc
        if not (min_expected_ndim <= data.ndim <= max_expected_ndim):
             raise ValueError(
                f"Non-uniform Data has {data.ndim} dimensions. Expected {min_expected_ndim} (if Nc=1 implicit) "
                f"or {max_expected_ndim} (if Nc explicit). First dim is NumPoints.")

        if f_vector.size != data_shape[1]: # Nf
            raise ValueError(
                f"Inconsistent frequency dimension for non-uniform data. "
                f"Data's second dimension (Nf, size {data_shape[1]}) "
                f"does not match length of f_vector ({f_vector.size}).")

        if num_dims > 0:
            # For file format, dimSize is [NumPoints, 1, 1, ...] for non-uniform
            file_dim_size_param = np.ones(num_dims, dtype=int)
            file_dim_size_param[0] = data_shape[0] # NumPoints
        elif data.ndim > 0: # 0D spatial (empty axis_coordinates), but data exists
            num_dims_for_file = 1 # File needs a dimension for NumPoints
            file_dim_size_param = np.array([data_shape[0]], dtype=int) # NumPoints
            warnings.warn("Non-uniform scan with 0 explicit axis_coordinates. "
                          "File will represent this as 1D scan with Data.shape[0] points.", UserWarning)
        else: # Should not happen due to earlier data.ndim check for non-uniform
            file_dim_size_param = np.array([], dtype=int)

        num_channels = data_shape[2] if data.ndim == 3 else 1

    num_f = f_vector.size
    # dimOrder for the file is always 0-indexed sequential (0, 1, ..., N-1)
    # This implies scan order is axis_coordinates[0], then axis_coordinates[1], etc.
    dim_order_for_file = np.arange(num_dims_for_file, dtype='<d')
    is_complex = np.iscomplexobj(data)

    # --- Validate and Prepare Header Structure ---
    _header_in = header_in if header_in is not None else {}
    header = {
        'header': str(_header_in.get('header', "")),
        'description': str(_header_in.get('description', "")),
        'device_name': str(_header_in.get('device_name', "")),
        'channel_names': [str(name) for name in _header_in.get('channel_names', [])]
    }

    if len(header['channel_names']) < num_channels:
        warnings.warn(
            f"Header 'channel_names' has {len(header['channel_names'])} elements, "
            f"but data has {num_channels} channels. Default names will be appended.", UserWarning)
        existing_len = len(header['channel_names'])
        for i in range(existing_len + 1, num_channels + 1):
            header['channel_names'].append(f"Channel {i}")
    elif len(header['channel_names']) > num_channels:
        warnings.warn(
            "Header 'channel_names' has too many elements. Extra names will be ignored.", UserWarning)
        header['channel_names'] = header['channel_names'][:num_channels]

    # --- Scan File Constants ---
    scan_file_code = 63474328.0
    scan_file_version = 1.0

    # --- Determine Output Filename ---
    if filename_in is None:
        root = tk.Tk()
        root.withdraw() # Hide the main tkinter window
        filename = filedialog.asksaveasfilename(
            title="Save Scan File",
            filetypes=[("Scan files", "*.scan"), ("All files", "*.*")],
            defaultextension=".scan"
        )
        if not filename:
            print("Save operation canceled by user.")
            return
    else:
        filename = filename_in

    base, ext = os.path.splitext(filename)
    if not ext:
        filename = base + ".scan"

    # --- Write to File ---
    try:
        with open(filename, 'wb') as fh:
            # Write Version Info
            fh.write(struct.pack('<d', scan_file_code))
            fh.write(struct.pack('<d', scan_file_version))

            # Write Scan File Header Strings
            _write_string_as_doubles(fh, header['header'])
            _write_string_as_doubles(fh, header['description'])
            _write_string_as_doubles(fh, header['device_name'])

            # Write Scan Data Format and Sizes
            fh.write(struct.pack('<d', float(is_uniform)))
            fh.write(struct.pack('<d', float(num_dims_for_file)))
            if num_dims_for_file > 0 : # Only write if there are dimensions
                fh.write(dim_order_for_file.astype('<d').tobytes())
                fh.write(file_dim_size_param.astype('<d').tobytes())
            fh.write(struct.pack('<d', float(num_channels)))

            # Write Channel Names
            for name in header['channel_names']:
                _write_string_as_doubles(fh, name)

            # Write Scan Coordinates and Frequencies Section Header
            fh.write(struct.pack('<d', float(num_f)))
            fh.write(struct.pack('<d', float(is_complex)))

            # Write Relative and Absolute Locations (Coordinates)
            if num_dims > 0: # Original number of spatial dimensions
                for coord_vec in axis_coordinates:
                    fh.write(coord_vec.astype('<d').tobytes()) # Relative
                for coord_vec in axis_coordinates:
                    fh.write(coord_vec.astype('<d').tobytes()) # Absolute (same as relative)
            elif not is_uniform and num_dims_for_file == 1 and num_dims == 0:
                # Non-uniform, 0D spatial input, but file needs 1D for NumPoints
                dummy_coord_vec = np.zeros(data_shape[0], dtype='<d') # Zeros for each point
                fh.write(dummy_coord_vec.tobytes()) # Relative
                fh.write(dummy_coord_vec.tobytes()) # Absolute

            # Write Frequency Vector
            fh.write(f_vector.astype('<d').tobytes())

            # --- Prepare Measurement Data for Writing ---
            data_to_process = np.copy(data) # Work with a copy

            if is_uniform:
                # Ensure data_to_process has explicit Nc dimension if it was 1
                if data_to_process.ndim == num_dims + 1: # Shape (S0,...,Sn-1, Nf)
                    data_to_process = data_to_process.reshape(data_shape[:num_dims] + (num_f, 1)) # (S0,...,Sn-1, Nf, Nc=1)
                
                # Permute Data from (S0,..,Sn-1,Nf,Nc) to (Nf,Nc,S0,..,Sn-1)
                permute_axes = (num_dims, num_dims + 1) + tuple(range(num_dims))
                data_to_process = np.transpose(data_to_process, axes=permute_axes)
                # Now data_to_process shape is (Nf, Nc, S0, S1, ..., Sn-1)

                # Apply Raster Scan Flip (modifies data_to_process in place via reshape views)
                # This loop iterates through logical dimensions D0, D1, ... D(n-2)
                # For each Di, it reshapes so Di is the 4th dim, and subsequent dims are combined.
                # Then it flips stripes in Di based on indices of the combined subsequent dims.
                if num_dims > 1: # Raster flip only applies if more than one spatial dimension
                    current_scan_shape = list(data_to_process.shape) # (Nf,Nc,S0,S1,...)
                    for i in range(num_dims - 1): # MATLAB ii from 1 to numDims-1
                        # dim_size_np contains [S0, S1, S2, ...]
                        prod_dims_before = int(np.prod(dim_size_np[0:i])) if i > 0 else 1
                        current_logical_dim_size = int(dim_size_np[i]) # Si
                        prod_dims_after = int(np.prod(dim_size_np[i+1:]))

                        reshape_target = (
                            num_f,
                            num_channels,
                            prod_dims_before,
                            current_logical_dim_size, # This is the dimension whose "columns" get flipped
                            prod_dims_after
                        )
                        # Reshape (potentially creates a view or copy)
                        data_reshaped_for_flip = data_to_process.reshape(reshape_target)
                        
                        # Flip along the 4th dimension (axis=3) for selected "columns" in 5th dim (axis=4)
                        if data_reshaped_for_flip.shape[4] > 0 : # Ensure there are elements in the 5th dim
                             # MATLAB: Data(:, :, :, :, 2:2:end) = flip(Data(:, :, :, :, 2:2:end), 4);
                             # Python: select based on 5th dim (axis=4), flip along 4th dim (axis=3)
                            data_reshaped_for_flip[:, :, :, :, 1::2] = np.flip(
                                data_reshaped_for_flip[:, :, :, :, 1::2], axis=3
                            )
                        
                        # Reshape back to (Nf, Nc, S0, S1, ...) for next iteration or final use
                        # This ensures data_to_process maintains the permuted main shape
                        data_to_process = data_reshaped_for_flip.reshape(current_scan_shape)
            else: # Non-uniform
                # Ensure data_to_process has explicit Nc dimension
                if data_to_process.ndim == 2: # Shape (NumPoints, Nf)
                    data_to_process = data_to_process.reshape(data_shape + (1,)) # (NumPoints, Nf, Nc=1)
                
                # Permute Data from (NumPoints,Nf,Nc) to (Nf,Nc,NumPoints)
                data_to_process = np.transpose(data_to_process, axes=(1, 2, 0))
                # Now data_to_process shape is (Nf, Nc, NumPoints)

            # Handle Complex Data: separate into [AllReals, AllImaginaries]
            if is_complex:
                real_part = np.real(data_to_process)
                imag_part = np.imag(data_to_process)
                # Flatten in Fortran (column-major) order and concatenate
                final_data_payload = np.concatenate(
                    (real_part.ravel(order='F'), imag_part.ravel(order='F'))
                )
            else:
                final_data_payload = data_to_process.ravel(order='F') # Flatten real data

            # Write the final data block
            fh.write(final_data_payload.astype('<d').tobytes())

        print(f"Scan file '{filename}' exported successfully.")

    except IOError as e:
        # Clean up partially written file? Not done by default.
        raise ValueError(f"Could not write to file '{filename}'. IO Error: {e}")
    except Exception as e:
        # Clean up partially written file?
        raise ValueError(f"An unexpected error occurred during scan export to '{filename}': {e}")