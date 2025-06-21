import numpy as np
import struct
import os
import re
import warnings
from typing import Tuple, List, Dict, Any, Optional, Union
import tkinter as tk
from tkinter import filedialog

def import_scan(num_output_dimensions: Optional[int] = None) -> Tuple:
    """
    Imports and parses a ".scan" file created by the amntl scanner program.

    Args:
        filename_in: Path to the file. If the file has no extension, ".scan"
                     will be automatically appended.
        num_output_dimensions: The number of output spatial dimension vectors
                               to return. If None, it's inferred from the
                               number of expected return values (requires careful
                               unpacking by the caller). Defaults to inferring.
                               It's generally safer to specify this explicitly if
                               you know the expected dimensionality.

    Returns:
        A tuple containing:
        - *coords: Variable number of 1D numpy arrays containing the coordinates
                   of each scan point for each spatial dimension (x, y, z, ...).
                   If the scan is uniform, each array contains unique, sorted,
                   uniformly increasing coordinates. Otherwise, each array
                   contains one element per scan point. The number of coordinate
                   arrays depends on `num_output_dimensions` or inferred value.
        - f: 1D numpy array of frequencies (in GHz, typically).
        - data: Numpy array containing the measurement data.
                If uniform: shape is (dim1_size, dim2_size, ..., num_freq, num_channels)
                If non-uniform: shape is (num_points, num_freq, num_channels)
        - header: Dictionary containing header information:
                  'header': str - User, date, time info.
                  'description': str - Scan description.
                  'device_name': str - Measurement device name.
                  'channel_names': List[str] - Names of channels.
                  'is_uniform': bool - Flag indicating if scan grid is uniform.
                  'named_arguments': Dict[str, str] - Parsed arguments from description.

    Raises:
        FileNotFoundError: If the scan file cannot be found.
        ValueError: If the file format or version is incorrect, or if the
                    header is corrupted, or if dimension mismatch occurs.

    Example Usage:
        # Assuming a 2D scan
        x, y, f, data, header = import_scan('my_scan.scan', num_output_dimensions=2)

        # Assuming a 3D scan
        x, y, z, f, data, header = import_scan('another_scan.scan', num_output_dimensions=3)

        # Inferring dimensions (less robust if caller expects fixed number)
        # *coords, f, data, header = import_scan('my_scan.scan')
        # x = coords[0]
        # y = coords[1]
    """

    # --- Argument Handling ---
    # Python doesn't have nargout directly. We use num_output_dimensions.
    # If not provided, we can't reliably infer it *before* reading the file.
    # The caller needs to handle the variable number of outputs correctly or provide the hint.
    requested_num_dims = num_output_dimensions

    # --- Open File ---
    # DRB changed to file dialog for better user experience
    filename = filedialog.askopenfilename(
        title="Select Scan File",
        filetypes=[("Scan files", "*.scan"), ("All files", "*.*")]
    )

    if not filename:
        return None  # User canceled the file dialog

    header_info = {}

    try:
        with open(filename, 'rb') as f:
            # --- Get Version Info ---
            scan_file_code = struct.unpack('<d', f.read(8))[0] # <d = little-endian double
            if scan_file_code != 63474328:
                raise ValueError("*.scan file type not recognized.")

            scan_file_version = struct.unpack('<d', f.read(8))[0]
            if scan_file_version != 1:
                raise ValueError("*.scan file version is not supported.")

            # --- Read Header Data From Scan File ---
            def read_string(file_handle):
                length = int(struct.unpack('<d', file_handle.read(8))[0])
                # Read length*doubles, convert each double to int, then to char
                chars = [chr(int(val)) for val in struct.unpack(f'<{length}d', file_handle.read(8 * length))]
                return "".join(chars)

            header_info['header'] = read_string(f)
            header_info['description'] = read_string(f)
            header_info['device_name'] = read_string(f)

            is_uniform_flag = struct.unpack('<d', f.read(8))[0]
            header_info['is_uniform'] = bool(is_uniform_flag)
            is_uniform = header_info['is_uniform'] # Local variable for convenience

            num_dims = int(struct.unpack('<d', f.read(8))[0])
            # Read dimOrder and dimSize (convert doubles to integers)
            dim_order_raw = struct.unpack(f'<{num_dims}d', f.read(8 * num_dims))
            dim_order = (1 + np.array(dim_order_raw)).astype(int) # 1-based in file, make 0-based? No, keep 1-based for now like MATLAB
            dim_size_raw = struct.unpack(f'<{num_dims}d', f.read(8 * num_dims))
            dim_size = np.array(dim_size_raw).astype(int)

            num_channels = int(struct.unpack('<d', f.read(8))[0])

            header_info['channel_names'] = [read_string(f) for _ in range(num_channels)]

            # --- Read Scan Coordinates and Frequencies ---
            num_f = int(struct.unpack('<d', f.read(8))[0])
            is_complex_flag = struct.unpack('<d', f.read(8))[0]
            is_complex = bool(is_complex_flag)

            axis_coordinates = []
            if is_uniform:
                for i in range(num_dims):
                    coords = np.frombuffer(f.read(8 * dim_size[i]), dtype='<d')
                    axis_coordinates.append(coords)
                # Discard absolute location
                f.read(8 * int(np.sum(dim_size)))
            else:
                # Non-uniform: dim_size[0] contains total number of points
                num_points = dim_size[0]
                for i in range(num_dims):
                     coords = np.frombuffer(f.read(8 * num_points), dtype='<d')
                     axis_coordinates.append(coords)
                # Discard absolute location
                f.read(8 * num_points * num_dims)

            # Read frequency vector (in GHz)
            freq_vector = np.frombuffer(f.read(8 * num_f), dtype='<d')

            # Check for premature EOF
            current_pos = f.tell()
            f.seek(0, os.SEEK_END)
            eof_pos = f.tell()
            f.seek(current_pos) # Go back

            # Need to estimate expected header size roughly, simple check might be needed
            # The MATLAB feof check happens *after* reading frequencies,
            # which might be too late if header fields were short.
            # We'll check before reading main data.

            # --- Read Scan Measurement Data ---
            num_spatial_points = int(np.prod(dim_size)) if is_uniform else dim_size[0]
            num_data_points = num_f * num_channels * num_spatial_points

            num_data_points_to_read = num_data_points * (1 + int(is_complex))

            data_bytes = f.read(8 * num_data_points_to_read)
            data_read = np.frombuffer(data_bytes, dtype='<d')
            # Check for missing data
            if len(data_read) < num_data_points_to_read:
                warnings.warn(
                    f"Scan file '{filename}' contains ({len(data_read)}) measurement values, "
                    f"which is less than the ({num_data_points_to_read}) expected. "
                    f"Data will be padded with zeros.", UserWarning)
                # Pad Missing Data With Zeros
                padded_data = np.zeros(num_data_points_to_read)
                padded_data[:len(data_read)] = data_read
                data_raw = padded_data
            else:
                data_raw = data_read

            # Check for too much data
            # Read one more byte (or attempt to)
            extra_data = f.read(1)
            if extra_data:
                warnings.warn(
                    f"Scan file '{filename}' contains more data than expected. "
                    f"The extra data will be ignored.", UserWarning)

            # --- Reorganize complex data ---
            if is_complex:
                #  # Assuming format [R1, R2, ..., RN, I1, I2, ..., IN] where N=num_data_points
                #  if len(data_raw) != 2 * num_data_points:
                #       # This might happen if padding occurred on incomplete complex data
                #      raise ValueError(f"Complex data size mismatch. Expected {2*num_data_points} values, got {len(data_raw)}")
                #  real_part = data_raw[:num_data_points]
                #  imag_part = data_raw[num_data_points:]
                #  data_complex = real_part + 1j * imag_part
                #  data = data_complex # Now proceed with complex data of size num_data_points
                try:
                    # Step 1: Reshape the flat raw data (read as 'data_raw')
                    # Target shape: (numF * numChannels, 2, num_spatial_points)
                    # Use order='F' to mimic MATLAB's column-major filling if necessary.
                    # Test both 'C' (default) and 'F'. 'F' is often needed for MATLAB compatibility.
                    reshaped_for_complex = data_raw.reshape((num_f * num_channels, 2, num_spatial_points), order='F')

                    # Step 2: Create complex numbers by combining the two columns (Real=col 0, Imag=col 1)
                    # Result shape: (numF * numChannels, num_spatial_points)
                    data_complex_matlab_style = reshaped_for_complex[:, 0, :] + 1j * reshaped_for_complex[:, 1, :]


                    # Step 3: Final reshape to (num_f, num_channels, num_spatial_points)
                    # Again, try order='F' if needed to match MATLAB's final memory layout before permutation
                    data = data_complex_matlab_style.reshape((num_f, num_channels, num_spatial_points), order='F')
                    # print(f"DEBUG: Complex data reshaped MATLAB-style. Intermediate shape: {reshaped_for_complex.shape}, Final shape before permute: {data.shape}") # Debug
                except ValueError as reshape_error:
                    raise ValueError(f"Error reshaping complex data to match MATLAB structure. "
                                    f"Expected {num_data_points_to_read} elements for shape "
                                    f"({num_f * num_channels}, 2, {num_spatial_points}). Got {len(data_raw)}. Error: {reshape_error}") from reshape_error
                # --- END MATLAB LOGIC IMPLEMENTATION ---
            else:
                data = data_raw # Data is already real
                try:
                    # Should end up as (Nf, Nc, Nspatial) even if Nc=1
                    data = data.reshape((num_f, num_channels, num_spatial_points), order='F') # Try order='F' here too
                except ValueError as reshape_error:
                    raise ValueError(f"Error reshaping non-complex data. Expected {num_data_points} elements. Error: {reshape_error}")

    except struct.error as e:
        raise ValueError(f"Scan file '{filename}' header seems corrupted or incomplete. Error: {e}")
    except MemoryError as e:
         raise MemoryError(f"Not enough memory to read data from '{filename}'. Error: {e}")

    # --- Determine Actual Output Dimensions ---
    actual_num_dims = num_dims
    last_significant_dim_idx = np.where(dim_size > 1)[0]
    if last_significant_dim_idx.size > 0:
         last_significant_dim = last_significant_dim_idx[-1] + 1 # 1-based index
    else:
         last_significant_dim = 0 # No dimensions > 1

    if requested_num_dims is None:
        # If not specified, default to the number of dimensions with size > 1
        # or at least 1 if all are size 1.
        final_num_output_dims = max(1, last_significant_dim) if actual_num_dims > 0 else 0
        # Warn if this default differs from actual file dims
        if final_num_output_dims != actual_num_dims and actual_num_dims > 0 :
             warnings.warn(
                f"Number of output dimensions was not specified. Inferring {final_num_output_dims} "
                f"based on significant dimensions found ({last_significant_dim}). "
                f"The file actually has {actual_num_dims} dimension(s). "
                f"Specify 'num_output_dimensions' for explicit control.", UserWarning)
    else:
        final_num_output_dims = requested_num_dims

    # --- Check File Dimensions vs Requested Output Dimensions ---
    if final_num_output_dims < last_significant_dim:
        raise ValueError(
            f"Requested number of output dimensions ({final_num_output_dims}) is "
            f"less than the last significant dimension in the scan file ({last_significant_dim}).")

    if final_num_output_dims < actual_num_dims:
         # Check if the extra dimensions are singleton
        if np.all(dim_size[final_num_output_dims:] == 1):
            # Remove singleton dimensions from internal tracking
            actual_num_dims = final_num_output_dims
            # Filter dim_order and dim_size - careful with 1-based dim_order
            valid_order_indices = dim_order <= actual_num_dims
            dim_order = dim_order[valid_order_indices]
            dim_size = dim_size[:actual_num_dims]
        else:
             # This case is prevented by the check against last_significant_dim above
             pass # Should not be reached

    if final_num_output_dims > actual_num_dims:
         warnings.warn(
            f"Requested number of output dimensions ({final_num_output_dims}) is greater "
            f"than the number of dimensions in the scan file ({actual_num_dims}). "
            f"Extra singleton dimensions will be added to the output coordinates.", UserWarning)

    # --- Prepare Output Coordinates ---
    output_coords = []
    for i in range(actual_num_dims):
        output_coords.append(axis_coordinates[i])

    # Add remaining requested coordinate vectors as single points (0) or arrays of zeros
    for i in range(actual_num_dims, final_num_output_dims):
        if is_uniform:
            output_coords.append(np.array([0.0])) # Singleton dimension coordinate
        else:
            # Need same number of points as other non-uniform coords
            num_pts_non_uniform = dim_size[0] if not is_uniform else 1 # Fallback
            if not is_uniform and actual_num_dims > 0:
                 num_pts_non_uniform = len(axis_coordinates[0])
            elif not is_uniform: # 0 actual dims but non-uniform requested? Unlikely.
                 num_pts_non_uniform = dim_size[0] if dim_size.size > 0 else 1

            output_coords.append(np.zeros(num_pts_non_uniform))

    # --- Reorganize Data (Final Permutation/Reshape) ---
    # (Keep the existing logic here for uniform/non-uniform, BUT REMOVE the np.swapaxes at the end)
    # AND implement the RASTER FLIP logic correctly if needed.
    if is_uniform:
        # --- Implement Raster Scan Flip ---
        for ii in range(actual_num_dims -1):
            matlab_ii = i # Equivalent 1-based loop counter for MATLAB logic

            # Get sizes corresponding to the desired OUTPUT dimension order
            # dim_order is 1-based [o1, o2,...], dim_size is 0-based [s1, s2,...]
            # We need sizes in the order specified by dim_order
            try:
                # Use 0-based indexing for dim_size, subtracting 1 from dim_order values
                output_dim_size_ordered = dim_size[dim_order - 1]
            except IndexError:
                raise IndexError(f"Error accessing dim_size with indices from dim_order. dim_order={dim_order}, dim_size len={len(dim_size)}")

            # Calculate size of "earlier" dimensions product (dims 1 to ii-1 in OUTPUT order)
            # Python slice indices: 0 to matlab_ii-2
            if matlab_ii == 1: # First iteration (i=0)
                size_dim3 = 1
            else:
                # Slice output_dim_size_ordered using 0-based indices
                size_dim3 = np.prod(output_dim_size_ordered[0 : matlab_ii - 1])

            # Get size of the "current" dimension (dim ii in OUTPUT order)
            # Python index: matlab_ii-1
            size_dim4 = output_dim_size_ordered[matlab_ii - 1]

            # Target shape for reshape, using -1 for automatic calculation
            target_shape = (num_f, num_channels, int(size_dim3), int(size_dim4), -1)

            # print(f"DEBUG: Raster flip reshape. Loop i={i} (MATLAB ii={matlab_ii}). Target Shape={target_shape}")
            Nx = dim_size[0]
            Ny = dim_size[1]
            target_shape_for_flip = (num_f, num_channels, 1, Ny, Nx)
            # Reshape temp_data (ensure temp_data has the expected dimensions before this)
            # Need to handle initial reshape from flat if necessary (outside or at i=0)
            try:
                # --- Alternative Reshape - Mimic Column-Major Filling ---
                # 1. Ensure input 'data' is contiguous in Fortran order if possible
                #    (It should be if the previous reshape used order='F')
                if not data.flags['F_CONTIGUOUS']:
                    # print("Warning: Input data not F-contiguous, copying.")
                    input_data_for_reshape = np.asfortranarray(data) # Make it F-contiguous
                else:
                    input_data_for_reshape = data

                # 2. Create the target array with Fortran order
                temp_data_reshaped = np.empty(target_shape_for_flip, dtype=input_data_for_reshape.dtype, order='F')

                # 3. Fill the target array column-major style
                # Flatten the input in Fortran order, then reshape target also in Fortran order
                # This should ensure elements are placed compatibly with MATLAB's reshape
                temp_data_reshaped[:] = input_data_for_reshape.flatten('F').reshape(target_shape_for_flip, order='F')
                # The [:] ensures we fill the existing array

                # --- End Alternative Reshape ---

                # print(f"DEBUG: Reshaped (Manual F-Order) for flip operation: {temp_data_reshaped.shape}") # EXPECT (51, 1, 1, 71, 141)

            except ValueError as e:
                raise Exception(f"ERROR: Reshape failed. Current shape: {data.shape}, Target: {target_shape}. Error: {e}")

            temp_data_reshaped[:, :, :, :, 1::2] = np.flip(temp_data_reshaped[:, :, :, :, 1::2], axis=3)
            # print("After raster flips:", temp_data_reshaped.shape)

            shape = [num_f, num_channels] + [dim_size[j] for j in dim_order-1]
            data = temp_data_reshaped.reshape(shape)
            # print(data.shape)
            # print("After reshape to full grid:", data.shape)

            if data.shape[1] == 1:
                data = np.squeeze(data, axis=1)

            # Transpose from (F, Y, X) → (X, Y, F)
            data = np.transpose(data, axes=(2, 1, 0))
            # print(data.shape)

    else:
        data = np.transpose(data, axes=(2, 0, 1))


    # --- Assemble Final Output Tuple --- #
    output_tuple = tuple(output_coords) + (freq_vector, data, header_info)

    return output_tuple